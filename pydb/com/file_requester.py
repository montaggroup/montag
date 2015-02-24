from collections import deque
import logging
import os
from twisted.internet import reactor
import traceback

MaxParallelFileRequests = 5

logger = logging.getLogger("com.file_requester")
from tempfile import mkstemp


class FileInTransfer(object):
    def __init__(self, file_hash, file_extension):
        self.file_hash = file_hash
        self.file_extension = file_extension

        # remove non-ascii characters from extension to enable the use of ascii-only-filename filesystems
        if self.file_extension is not None:
            self.file_extension = self.file_extension.encode('ascii', errors='ignore')

        (handle, self.file_name) = mkstemp(suffix='.' + self.file_extension)

        logger.info(u"Creating file: {}".format(self.file_name))
        self.file_object = os.fdopen(handle, "wb")

    def write(self, data):
        logger.debug("Writing {} bytes into file".format(len(data)))
        self.file_object.write(data)

    def close(self):
        if self.file_object is not None:
            self.file_object.close()
            self.file_object = None


class FileRequester(object):
    def __init__(self, main_db, comservice, file_inserter):
        self.main_db = main_db
        self.file_inserter = file_inserter
        self.comservice = comservice

        self.hashes_to_request_set = set()
        self.hashes_to_request = deque([])
        self.requested_hashes = deque([])

        self.current_transfer = None

        self.number_files_requested_total = 0
        self.number_files_downloaded = 0
        self.number_negative_file_replies = 0

        self.file_progress_callback = None
        self._completion_callback = None
        self._failure_callback = None

        self._session = None
        self._friend_id = None

    def queue_download_file(self, file_hash):
        if file_hash not in self.hashes_to_request_set:
            self.hashes_to_request.append(file_hash)
            self.hashes_to_request_set.add(file_hash)
            self.number_files_requested_total += 1

    def queue_length(self):
        return self.number_files_requested_total

    def set_file_progress_callback(self, cb):
        """ sets a function that is called when progress in file downloading is made.
        The callback will receive two arguments: (items_to_do, items_done)
            If a value is unknown, -1 will be used """
        self.file_progress_callback = cb

    def activate(self, session, friend_id, completion_callback, failure_callback):
        self._session = session
        self._friend_id = friend_id
        session.set_upper_layer(self)
        self._completion_callback = completion_callback
        self._failure_callback = failure_callback

        self._launch_file_requests()

    def _launch_file_requests(self):
        while len(self.requested_hashes) < MaxParallelFileRequests:
            if not self.hashes_to_request:
                if not self.requested_hashes:
                    logger.debug("No more files to request, waiting for last insert to complete")
                    self.file_inserter.wait_for_insert_to_complete()
                    self._completion_callback()
                return

            file_hash = self.hashes_to_request.popleft()

            lock_result = self.comservice.lock_file_for_fetching(file_hash)
            if lock_result == "locked":
                logger.info("Fetching file with hash {}".format(file_hash))
                self.requested_hashes.append(file_hash)
                self._session.request_file(file_hash)
            elif lock_result == "busy":
                logger.info("File {} currently locked, putting it to the end of the queue".format(file_hash))
                self.hashes_to_request.append(file_hash)
                query_delay = 1.0 / len(self.hashes_to_request)
                reactor.callLater(query_delay, self._launch_file_requests)
                return
            elif lock_result == "completed":
                logger.info("File transfer for hash {} already completed".format(file_hash))
            else:
                raise ValueError("Unknown file hash lock result: '{}'".format(lock_result))

    def _negative_file_reply_received(self, file_hash):
        logger.info("Negative reply for hash %s" % file_hash)
        expected_hash = self.requested_hashes.popleft()
        if file_hash != expected_hash:
            raise ValueError("Request order error, requested hash {} but got {}".format(expected_hash, file_hash))

        self.number_negative_file_replies += 1
        self.comservice.release_file_after_fetching(file_hash, success=False)

        if self.current_transfer is not None:
            raise ValueError("Answer order error, was expecting more parts for hash {}, but got not content".format(
                             self.current_transfer.file_hash))

    def _finish_multipart_transfer(self):
        self.current_transfer.close()
        self.number_files_downloaded += 1
        logger.info("Adding file via {}".format(self.current_transfer.file_name))
        self.file_inserter.insert_file_in_background(self.current_transfer.file_name,
                                                     self.current_transfer.file_extension,
                                                     self.current_transfer.file_hash)
        self.current_transfer = None

    def _start_multipart_transfer(self, extension, file_hash):
        planned_hash = self.requested_hashes.popleft()
        if file_hash != planned_hash:
            raise ValueError("Request order error, requested hash {} but got {}".
                             format(planned_hash, file_hash))

        self.current_transfer = FileInTransfer(file_hash, extension)

    def _positive_file_reply_received(self, file_hash, extension, content, more_parts_follow):
        logger.info("New file content, hash: {}, (Extension {}, more parts: {})".format(
                    file_hash, extension, more_parts_follow))

        if self.current_transfer is None:  # new file answer expected
            self._start_multipart_transfer(extension, file_hash)

        if self.current_transfer.file_hash != file_hash:
            raise ValueError("Answer order error, was expecting more parts for hash {}, "
                             "but got a part for hash {}".format(self.current_transfer.file_hash, file_hash))

        self.current_transfer.write(content)

        if not more_parts_follow:
            self._finish_multipart_transfer()

    def update_progress(self):
        if self.file_progress_callback is None:
            return
        self.file_progress_callback(self.number_files_requested_total,
                                    self.number_files_downloaded + self.number_negative_file_replies)

    def command_deliver_file_received(self, file_hash, extension, content, more_parts_follow):
        try:
            if content == "":
                self._negative_file_reply_received(file_hash)
            else:
                self._positive_file_reply_received(file_hash, extension, content, more_parts_follow)

        except ValueError as e:
            logger.error("Caught a value error: {} ({}) - {}".format(e.message, str(e), traceback.format_exc()))
            self._abort_mission()
            return

        self.update_progress()

        if not more_parts_follow or not content:
            logger.info("Requesting next file")
            self._launch_file_requests()

    def _abort_mission(self):
        logger.debug("Abort called, waiting for last insert to complete...")
        self.file_inserter.wait_for_insert_to_complete()

        if self.current_transfer is not None:
            self.comservice.release_file_after_fetching(self.current_transfer.file_hash, success=False)
        for file_hash in self.requested_hashes:
            self.comservice.release_file_after_fetching(file_hash, success=False)

        self._failure_callback()

    def session_failed(self, reason):
        logger.error("sessionFailed: {}".format(reason))
        self._abort_mission()

    def session_lost(self, reason):
        logger.error("The session was lost uncleanly: {}".format(reason))
        self._abort_mission()

from collections import deque
import logging
import os
from twisted.internet import reactor
import traceback

MaxParallelFileRequests = 5

logger = logging.getLogger("com.file_requester")
from tempfile import mkstemp


class FileRequester(object):
    def __init__(self, main_db, comservice, file_inserter):
        self.main_db = main_db
        self.hashes_to_request_set = set()
        self.hashes_to_request = deque([])
        self.requested_hashes = deque([])

        self.hash_of_transfer_in_progress = None  # for multi-part-transfers
        self.handle_of_file_in_progress = None  # for multi-part-transfers
        self.name_of_file_in_progress = None  # for multi-part-transfers

        self.number_files_requested_total = 0
        self.number_files_downloaded = 0
        self.number_negative_file_replies = 0

        self.file_progress_callback = None
        self._completion_callback = None
        self._failure_callback = None

        self._session = None
        self._friend_id = None

        self.file_inserter = file_inserter

        self.comservice = comservice

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
            logger.error("Request order error, requested hash %s but got %s" % (expected_hash, file_hash))
            self._abort_mission()
            return

        self.number_negative_file_replies += 1
        self.comservice.release_file_after_fetching(file_hash, False)

        if self.hash_of_transfer_in_progress is not None:
            logger.error("Answer order error, was expecting more parts for hash %s, but got not content" %
                         self.hash_of_transfer_in_progress)

    def _finish_multipart_transfer(self, extension, file_hash):
        self.handle_of_file_in_progress.close()
        self.handle_of_file_in_progress = None
        self.hash_of_transfer_in_progress = None
        completed_file_name = self.name_of_file_in_progress
        self.name_of_file_in_progress = None
        self.number_files_downloaded += 1
        logger.info("Adding file via %s" % completed_file_name)
        self.file_inserter.insert_file_in_background(completed_file_name, extension, file_hash)

    def _start_multipart_transfer(self, extension, file_hash):
        self.hash_of_transfer_in_progress = self.requested_hashes.popleft()
        if file_hash != self.hash_of_transfer_in_progress:
            error_string = "Request order error, requested hash %s but got %s" \
                           % (self.hash_of_transfer_in_progress, file_hash)
            raise ValueError(error_string)

        (handle, self.name_of_file_in_progress) = mkstemp(suffix='.' + extension)
        logger.info(u"Creating file: {}".format(self.name_of_file_in_progress))
        self.handle_of_file_in_progress = os.fdopen(handle, "w")

    def _positive_file_reply_received(self, file_hash, extension, content, more_parts_follow):
        # remove non-ascii characters from extension to enable the use of ascii-only-filename filesystems
        if extension is not None:
            extension = extension.encode('ascii', errors='ignore')

        if self.hash_of_transfer_in_progress is None:  # new file answer expected
            try:
                self._start_multipart_transfer(extension, file_hash)
            except ValueError as e:
                logger.error("Caught a value error: {} ({}) - {}".format(e.message, str(e), traceback.format_exc()))
                self._abort_mission()
                return
        else:  # this should be a continuation message
            if self.hash_of_transfer_in_progress != file_hash:
                logger.error("Answer order error, was expecting more parts for hash %s, "
                             "but got a part for hash %s" %
                             (self.hash_of_transfer_in_progress, file_hash))
                self._abort_mission()
                return

        logger.info("Writing {} bytes ({} bytes encoded) into file".format(len(content), len(content)))
        self.handle_of_file_in_progress.write(content)

        if not more_parts_follow:
            self._finish_multipart_transfer(extension, file_hash)

    def command_deliver_file_received(self, file_hash, extension, content, more_parts_follow):
        if content == "":
            self._negative_file_reply_received(file_hash)
        else:
            logger.info("New file content, hash: %s, (Extension %s, more parts: %s)"
                        % (file_hash, extension, more_parts_follow))
            self._positive_file_reply_received(file_hash, extension, content, more_parts_follow)

        if self.file_progress_callback is not None:
            self.file_progress_callback(self.number_files_requested_total,
                                        self.number_files_downloaded + self.number_negative_file_replies)

        if not more_parts_follow or not content:
            logger.info("Requesting next file")
            self._launch_file_requests()

    def _abort_mission(self):
        self.file_inserter.wait_for_insert_to_complete()

        if self.hash_of_transfer_in_progress is not None:
            self.comservice.release_file_after_fetching(self.hash_of_transfer_in_progress, False)
        for file_hash in self.requested_hashes:
            self.comservice.release_file_after_fetching(file_hash, False)

        self._failure_callback()

    def session_failed(self, reason):
        logger.error("sessionFailed: %s", reason)
        self._abort_mission()

    def session_lost(self, reason):
        logger.error("The session was lost uncleanly: %s " % reason)
        self._abort_mission()

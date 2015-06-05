import logging
import os
from collections import deque

logger = logging.getLogger('file_send_queue')

FILE_TRANSFER_CHUNK_SIZE = 1024 * 1024


class FileSendQueue(object):
    def __init__(self, session, file_server, report_progress, reactor):
        self.session = session
        self.file_server = file_server
        self.report_progress = report_progress
        self.reactor = reactor

        self.is_transfer_in_progress = False
        self.queue = deque()
        self.paused = False
        self.file_in_progress = None

    def enqueue(self, file_hash):
        is_idle = not self.queue and not self.is_transfer_in_progress
        self.queue.append(file_hash)
        
        if is_idle:
            self._check_for_more_work()

    def pause_sending(self):
        self.paused = True

    def resume_sending(self):
        self.paused = False
        self._check_for_more_work()

    def _check_for_more_work_later(self):
        self.reactor.callLater(0, self._check_for_more_work)

    def _check_for_more_work(self):
        if self.paused:
            return

        if self.is_transfer_in_progress:  # try to complete transfer
            self._send_next_chunk()
            return

        if self.queue:
            next_hash = self.queue.popleft()
            self._begin_sending(next_hash)

    def _send_next_chunk(self):
        chunk = self.next_chunk
        self.next_chunk = self.file_in_progress.read(FILE_TRANSFER_CHUNK_SIZE)
        more_chunks_follow = bool(self.next_chunk)

        if not more_chunks_follow:
            self.is_transfer_in_progress = False
            self.file_in_progress.close()
            self.file_in_progress = None
            self.report_progress(number_files_increment=1)

        self.session.deliver_file(self.file_hash_in_progress,
                                  self.file_extension_in_progress,
                                  chunk,
                                  more_parts_follow=more_chunks_follow)
        self._check_for_more_work_later()

    def _begin_sending(self, file_hash):
        local_path = self.file_server.get_local_file_path(file_hash)

        if not local_path:
            logger.info("Sending negative reply for hash {}".format(file_hash))
            self.session.deliver_file(file_hash, extension="", content="", more_parts_follow=False)
            return

        file_extension_with_dot = os.path.splitext(local_path)[1]
        file_extension = file_extension_with_dot[1:]

        logging.info("Sending file {}".format(file_hash))
        self.is_transfer_in_progress = True
        self.file_hash_in_progress = file_hash
        self.file_extension_in_progress = file_extension

        self.file_in_progress = open(local_path, 'rb')
        self.next_chunk = self.file_in_progress.read(FILE_TRANSFER_CHUNK_SIZE)
        self._send_next_chunk()


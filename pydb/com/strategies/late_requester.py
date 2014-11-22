from . import *

import logging
logger = logging.getLogger('late_requester')

class LateRequester(Strategy):
    def __init__(self, metadata_requester, file_requester, provider, main_db):
        super(LateRequester, self).__init__()
        self._metadata_requester = metadata_requester
        self._file_requester = file_requester
        self._provider = provider
        self._main_db = main_db
        self._friend_id = None
        self._session = None
        self._completion_callback = None
        self._bulk_inserter = None

    def associated(self, session, friend_id, completion_callback, bulk_inserter):
        self._session = session
        self._friend_id = friend_id
        self._completion_callback = completion_callback
        self._bulk_inserter = bulk_inserter

        self._provider.set_providing_progress_callback(self.provider_reported_progress)
        self.provider_reported_progress(0, 0)
        self._provider.activate(self._session, self.provider_completed, self.any_requester_failed)

    def provider_completed(self):
        last_query_date_authors, last_query_date_tomes = self._main_db.get_friend_last_query_dates(self._friend_id)

        self._metadata_requester.set_document_progress_callback(self.metadata_requester_reported_progress)
        self.metadata_requester_reported_progress(0, 0)

        self._metadata_requester.activate(self._session, self._friend_id,
                                          self.metadata_requester_completed, self.any_requester_failed,
                                          self._bulk_inserter, last_query_date_authors, last_query_date_tomes)

    def metadata_requester_completed(self):
        prepare_file_requester(self._main_db, self._file_requester, default_max_files_to_request)
        self._file_requester.set_file_progress_callback(self.file_requester_reported_progress)
        self.file_requester_reported_progress(self._file_requester.queue_length(), 0)

        self._file_requester.activate(self._session, self._friend_id,
                                      self.file_requester_completed, self.any_requester_failed)

    def file_requester_completed(self):
        self._session.request_stop_providing()
        self._update_progress('completed', 0, 0)
        self._completion_callback()

    def any_requester_failed(self):
        logger.warning("A requester or provider failed to complete.")
        self._completion_callback()


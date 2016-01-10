# coding=utf-8
from . import *


class OnlyRequester(Strategy):
    def __init__(self, metadata_requester, file_requester, main_db):
        super(OnlyRequester, self).__init__()
        self._metadata_requester = metadata_requester
        self._file_requester = file_requester
        self._session = None
        self._completion_callback = None
        self._main_db = main_db
        self._friend_id = None

    def associated(self, session, friend_id, completion_callback, bulk_inserter):
        self._session = session
        self._friend_id = friend_id
        self._completion_callback = completion_callback

        last_query_date_authors, last_query_date_tomes = self._main_db.get_friend_last_query_dates(friend_id)

        self._metadata_requester.activate(self._session, self._friend_id,
                                          self.metadata_requester_completed, self.any_requester_failed,
                                          bulk_inserter, last_query_date_authors, last_query_date_tomes)

    def metadata_requester_completed(self):
        prepare_file_requester(self._main_db, self._file_requester, default_max_files_to_request)
        self._file_requester.activate(self._session, self._friend_id,
                                      self.file_requester_completed, self.any_requester_failed)

    def file_requester_completed(self):
        self._completion_callback()

    def any_requester_failed(self):
        self._completion_callback()

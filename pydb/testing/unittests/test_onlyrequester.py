# coding=utf-8
import unittest
import pydb.com.strategies.only_requester
import mock


class TestOnlyRequester(unittest.TestCase):
    def setUp(self):
        self.metadata_requester = mock.MagicMock()
        self.file_requester = mock.MagicMock()
        self.main_db = mock.MagicMock()

        self.last_query_date_authors = 44.0
        self.last_query_date_tomes = 55.0

        self.main_db.get_friend_last_query_dates.return_value = [self.last_query_date_authors,
                                                                 self.last_query_date_tomes]

        self.bulk_inserter = mock.MagicMock()
        self.friend_id = 5

        self.completion_callback = mock.MagicMock()

        self.strategy = pydb.com.strategies.only_requester.OnlyRequester(
            self.metadata_requester, self.file_requester, self.main_db)

    def test_empty(self):
        self.assertFalse(self.completion_callback.called)
        self.assertFalse(self.metadata_requester.activate.called)
        self.assertFalse(self.file_requester.activate.called)

    def test_associate_triggers_metadata_requester(self):
        session = mock.MagicMock()

        self.strategy.associated(session, self.friend_id, self.completion_callback, self.bulk_inserter)

        self.assertFalse(self.completion_callback.called)

        self.metadata_requester.activate.assert_called_once_with(session,
                                                                 self.friend_id,
                                                                 self.strategy.metadata_requester_completed,
                                                                 self.strategy.any_requester_failed,
                                                                 self.bulk_inserter,
                                                                 self.last_query_date_authors,
                                                                 self.last_query_date_tomes)

    def test_metadata_requester_complete_triggers_file_requester(self):
        session = mock.MagicMock()

        self.strategy.associated(session, self.friend_id, self.completion_callback, self.bulk_inserter)
        self.strategy.metadata_requester_completed()

        self.file_requester.activate.assert_called_once_with(session, self.friend_id,
                                                             self.strategy.file_requester_completed,
                                                             self.strategy.any_requester_failed)

    def test_requester_complete_triggers_completion_callback(self):
        session = mock.MagicMock()

        self.strategy.associated(session, self.friend_id, self.completion_callback, self.bulk_inserter)
        self.strategy.metadata_requester_completed()
        self.strategy.file_requester_completed()

        self.completion_callback.assert_called_once_with()


if __name__ == '__main__':
    unittest.main()

import unittest
import pydb.com.strategies.early_requester
import mock


class test_early_requester(unittest.TestCase):
    def setUp(self):
        self.provider = mock.MagicMock()
        self.metadata_requester = mock.MagicMock()
        self.file_requester = mock.MagicMock()

        self.completion_callback = mock.MagicMock()

        self.main_db = mock.MagicMock()

        self.last_query_date_authors = 44.0
        self.last_query_date_tomes = 55.0

        self.main_db.get_friend_last_query_dates.return_value = [self.last_query_date_authors,
                                                                 self.last_query_date_tomes]

        self.bulk_inserter = mock.MagicMock()
        self.friend_id = 5

        self.strategy = pydb.com.strategies.early_requester.EarlyRequester(
            self.metadata_requester, self.file_requester, self.provider, self.main_db)

    def test_empty(self):
        self.assertFalse(self.completion_callback.called)
        self.assertFalse(self.metadata_requester.activate.called)
        self.assertFalse(self.file_requester.activate.called)
        self.assertFalse(self.provider.activate.called)

    def test_associate_triggers_metadata_requester(self):
        session = mock.MagicMock()

        self.strategy.associated(session, self.friend_id, self.completion_callback, self.bulk_inserter)

        self.assertFalse(self.completion_callback.called)
        self.assertFalse(self.provider.activate.called)
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

        self.assertFalse(self.completion_callback.called)
        self.file_requester.activate.assert_called_once_with(session, self.friend_id,
                                                             self.strategy.file_requester_completed,
                                                             self.strategy.any_requester_failed)

    def test_file_requester_complete_triggers_provider(self):
        session = mock.MagicMock()

        self.strategy.associated(session, self.friend_id, self.completion_callback, self.bulk_inserter)
        self.strategy.metadata_requester_completed()
        self.strategy.file_requester_completed()

        self.assertFalse(self.completion_callback.called)
        self.provider.activate.assert_called_once_with(session, self.strategy.provider_completed, self.strategy.any_requester_failed)

    def test_file_requester_complete_triggers_stop_providing_message(self):
        session = mock.MagicMock()

        self.strategy.associated(session, self.friend_id, self.completion_callback, self.bulk_inserter)
        self.strategy.metadata_requester_completed()
        self.strategy.file_requester_completed()

        session.request_stop_providing.assert_called_once_with()

    def test_all_complete_triggers_completion_callback(self):
        session = mock.MagicMock()

        self.strategy.associated(session, self.friend_id, self.completion_callback, self.bulk_inserter)
        self.strategy.metadata_requester_completed()
        self.strategy.file_requester_completed()
        self.strategy.provider_completed()

        self.completion_callback.assert_called_once_with()


if __name__ == '__main__':
    unittest.main()

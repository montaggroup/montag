import unittest
import pydb.com.strategies.late_requester
import mock


class StrategyProgressTracker():
    def __init__(self):
        self.reported_current_phase_id = None
        self.reported_current_phase_name = None
        self.reported_current_number_items_to_do = None
        self.reported_number_items_done = None

    def spy_on_strategy(self, strategy):
        def update_progress(current_phase_id, number_items_to_do, number_items_done):
            self.reported_current_phase_id = current_phase_id
            self.reported_current_phase_name = pydb.com.strategies.strategy_phase_name(current_phase_id)
            self.reported_current_number_items_to_do = number_items_to_do
            self.reported_number_items_done = number_items_done

        strategy.set_progress_callback(update_progress)


class TestLateRequester(unittest.TestCase):
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

        self.strategy = pydb.com.strategies.late_requester.LateRequester(
            self.metadata_requester, self.file_requester, self.provider, self.main_db)
        self.strategy_progress_tracker = StrategyProgressTracker()
        self.strategy_progress_tracker.spy_on_strategy(self.strategy)

    def test_empty(self):
        self.assertFalse(self.provider.activate.called)
        self.assertFalse(self.metadata_requester.activate.called)
        self.assertFalse(self.file_requester.activate.called)
        self.assertFalse(self.completion_callback.called)

    def test_associate_triggers_provider(self):
        session = mock.MagicMock()

        self.strategy.associated(session, self.friend_id, self.completion_callback, self.bulk_inserter)

        self.assertFalse(self.completion_callback.called)
        self.assertFalse(self.metadata_requester.activate.called)
        self.assertTrue(self.provider.activate.called)
        self.assertEquals('providing', self.strategy_progress_tracker.reported_current_phase_name)

    def test_provider_complete_triggers_metadata_requester(self):
        session = mock.MagicMock()

        self.strategy.associated(session, self.friend_id, self.completion_callback, self.bulk_inserter)
        self.strategy.provider_completed()

        self.assertFalse(self.completion_callback.called)
        self.metadata_requester.activate.assert_called_once_with(session,
                                                                 self.friend_id,
                                                                 self.strategy.metadata_requester_completed,
                                                                 self.strategy.any_requester_failed,
                                                                 self.bulk_inserter,
                                                                 self.last_query_date_authors,
                                                                 self.last_query_date_tomes)
        self.assertEquals('requesting_metadata', self.strategy_progress_tracker.reported_current_phase_name)

    def test_metadata_requester_complete_triggers_file_requester(self):
        session = mock.MagicMock()

        self.strategy.associated(session, self.friend_id, self.completion_callback, self.bulk_inserter)
        self.strategy.provider_completed()
        self.strategy.metadata_requester_completed()

        self.assertFalse(self.completion_callback.called)
        self.file_requester.activate.assert_called_once_with(session, self.friend_id,
                                                             self.strategy.file_requester_completed,
                                                             self.strategy.any_requester_failed)
        self.assertEquals('requesting_files', self.strategy_progress_tracker.reported_current_phase_name)

    def test_all_complete_triggers_completion_callback(self):
        session = mock.MagicMock()

        self.strategy.associated(session, self.friend_id, self.completion_callback, self.bulk_inserter)
        self.strategy.provider_completed()
        self.strategy.metadata_requester_completed()
        self.strategy.file_requester_completed()

        self.completion_callback.assert_called_once_with()
        self.assertEquals('completed', self.strategy_progress_tracker.reported_current_phase_name)

    def test_all_complete_triggers_stop_providing_message(self):
        session = mock.MagicMock()

        self.strategy.associated(session, self.friend_id, self.completion_callback, self.bulk_inserter)
        self.strategy.provider_completed()
        self.strategy.metadata_requester_completed()
        self.strategy.file_requester_completed()

        session.request_stop_providing.assert_called_once_with()


class TestLateRequesterPartialSetup(unittest.TestCase):
    def setUp(self):
        pass

    def test_without_progress_callback_does_not_crash(self):
        self.provider = mock.MagicMock()

        self.strategy = pydb.com.strategies.late_requester.LateRequester(
            None, None, self.provider, None)

        self.strategy.associated(None, None, None, None)


if __name__ == '__main__':
    unittest.main()

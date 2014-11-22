import unittest
import pydb.com.strategies.only_provider
import mock


class TestOnlyProvider(unittest.TestCase):
    def setUp(self):
        self.provider = mock.MagicMock()
        self.metadata_requester = mock.MagicMock()
        self.completion_callback = mock.MagicMock()

        self.main_db = mock.MagicMock()
        self.friend_id = 5

        self.strategy = pydb.com.strategies.only_provider.OnlyProvider(
            self.provider, self.main_db)

    def test_empty(self):
        self.assertFalse(self.provider.activate.called)
        self.assertFalse(self.completion_callback.called)

    def test_associate_triggers_provider(self):
        session = mock.MagicMock()

        self.strategy.associated(session, self.friend_id, self.completion_callback, None)

        self.assertFalse(self.completion_callback.called)
        self.provider.activate.assert_called_once_with(session, self.strategy.provider_completed, self.strategy.any_requester_failed)

    def test_provider_complete_triggers_completion_callback(self):
        session = mock.MagicMock()

        self.strategy.associated(session, self.friend_id, self.completion_callback, None)
        self.strategy.provider_completed()

        self.completion_callback.assert_called_once_with()

if __name__ == '__main__':
    unittest.main()

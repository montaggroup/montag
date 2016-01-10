# coding=utf-8
import unittest
import pydb.com.provider
import mock


class TestProvider(unittest.TestCase):
    def setUp(self):
        self.db = None
        self.file_server = None
        self.provider = pydb.com.provider.Provider(self.db, self.file_server)

    def test_empty(self):
        pass

    def test_activate_changes_upper_layer_of_session(self):
        session = mock.MagicMock()
        callback = mock.MagicMock()
        self.provider.activate(session, callback, callback)
        session.set_upper_layer.assert_called_once_with(self.provider)

        self.assertFalse(callback.called)

    def test_stop_providing_command_triggers_completion_callback(self):
        session = mock.MagicMock()
        callback = mock.MagicMock()
        self.provider.activate(session, callback, callback)
        self.provider.command_stop_providing_received()

        callback.assert_called_once_with()




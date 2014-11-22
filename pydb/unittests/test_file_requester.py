import unittest
import pydb.com.file_requester
import mock


class TestFileRequester(unittest.TestCase):
    def setUp(self):
        self.db = None
        self.comservice = mock.MagicMock()
        self.requester = pydb.com.file_requester.FileRequester(self.db, self.comservice)
        self.friend_id = 1
        self.session = mock.MagicMock()
        self.callback = mock.MagicMock()
        self.failure_callback = mock.MagicMock()

    def test_empty(self):
        pass

    def test_activate_changes_upper_layer_of_session(self):
        self.requester.activate(self.session, self.friend_id, self.callback, self.failure_callback)
        self.session.set_upper_layer.assert_called_once_with(self.requester)

    def test_empty_file_list_triggers_completion_callback(self):
        self.requester.activate(self.session, self.friend_id, self.callback, self.failure_callback)
        self.callback.assert_called_once_with()


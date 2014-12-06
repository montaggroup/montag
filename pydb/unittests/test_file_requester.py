import unittest
import pydb.com.file_requester
import mock


class TestFileRequester(unittest.TestCase):
    def setUp(self):
        self.db = None
        self.comservice = mock.MagicMock()
        self.file_inserter = mock.MagicMock()
        pydb.com.file_requester.FileRequester.MaxParallelFileRequests = 5
        self.requester = pydb.com.file_requester.FileRequester(self.db, self.comservice, self.file_inserter)
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

    def test_when_7_downloads_are_scheduled_all_7_will_be_executed_eventually(self):

        self.comservice.lock_file_for_fetching.return_value = 'locked'

        self.requester.queue_download_file('hash1')
        self.requester.queue_download_file('hash2')
        self.requester.queue_download_file('hash3')
        self.requester.queue_download_file('hash4')
        self.requester.queue_download_file('hash5')
        self.requester.queue_download_file('hash6')
        self.requester.queue_download_file('hash7')

        self.requester.activate(self.session, self.friend_id, self.callback, self.failure_callback)

        self.session.request_file.assert_any_call('hash1')
        self.requester.command_deliver_file_received('hash1', 'ext1', 'c1', False)

        self.session.request_file.assert_any_call('hash2')
        self.requester.command_deliver_file_received('hash2', 'ext1', 'c1', False)

        self.session.request_file.assert_any_call('hash3')
        self.requester.command_deliver_file_received('hash3', 'ext1', 'c1', False)

        self.session.request_file.assert_any_call('hash4')
        self.requester.command_deliver_file_received('hash4', 'ext1', 'c1', False)

        self.session.request_file.assert_any_call('hash5')
        self.requester.command_deliver_file_received('hash5', 'ext1', 'c1', False)

        self.session.request_file.assert_any_call('hash6')
        self.requester.command_deliver_file_received('hash6', 'ext1', 'c1', False)

        self.assertFalse(self.callback.call_count)
        self.session.request_file.assert_any_call('hash7')
        self.requester.command_deliver_file_received('hash7', 'ext1', 'c1', False)
        self.callback.assert_called_once_with()
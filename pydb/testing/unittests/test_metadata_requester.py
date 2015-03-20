import unittest
import pydb.com.metadata_requester
import mock


class TestMetadataRequester(unittest.TestCase):
    def setUp(self):
        self.db = None
        self.requester = pydb.com.metadata_requester.MetadataRequester(self.db)
        self.friend_id = 1
        self.last_author_change_date = 10.0
        self.last_tome_change_date = 11.0

        self.session = mock.MagicMock()
        self.callback = mock.MagicMock()
        self.inserter = mock.MagicMock()
        self.failure_callback = mock.MagicMock()

    def test_empty(self):
        pass

    def test_activate_changes_upper_layer_of_session(self):
        self.requester.activate(self.session, self.friend_id, self.callback, self.failure_callback,
                                self.inserter,
                                self.last_author_change_date, self.last_tome_change_date)
        self.session.set_upper_layer.assert_called_once_with(self.requester)



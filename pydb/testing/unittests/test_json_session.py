import json
import unittest
import pydb.com.jsonsession
import mock


class TestJsonSession(unittest.TestCase):
    def setUp(self):
        self.initial_upper_layer = mock.MagicMock()
        self.session = pydb.com.jsonsession.JsonSession(self.initial_upper_layer)
        self.friend_id = 5

    def test_empty(self):
        pass

    def test_secure_channel_established_is_reported_to_upper_layer(self):
        self.session.secure_channel_established(self.friend_id)
        self.initial_upper_layer.session_established.assert_called_once_with(self.friend_id)

    def test_secure_channel_established_is_reported_to_changed_upper_layer(self):
        new_upper_layer = mock.MagicMock()

        self.session.set_upper_layer(new_upper_layer)
        self.session.secure_channel_established(self.friend_id)

        new_upper_layer.session_established.assert_called_once_with(self.friend_id)
        self.assertFalse(self.initial_upper_layer.session_established.called)

    def build_message_string(self, command, args):
        message_dict = {'command': command,
                        'args': args}
        message_string = json.dumps(message_dict)
        return message_string

    def feed_message_to_session(self, command, args):
        message_string = self.build_message_string(command, args)
        self.session.message_received(message_string)

    def test_command_setNumberDocuments(self):
        self.feed_message_to_session('setNumberDocuments', [42, 23])
        self.initial_upper_layer.command_set_number_documents_entries_received.assert_called_once_with(42, 23)

    def test_command_stopProviding(self):
        self.feed_message_to_session('stopProviding', [])
        self.initial_upper_layer.command_stop_providing_received.assert_called_once_with()

    def test_stopProviding(self):
        lower_layer = mock.MagicMock()
        self.session.set_lower_layer(lower_layer)
        self.session.request_stop_providing()

        args = lower_layer.send_message.call_args
        first_arg_of_first_call = args[0][0]
        message = json.loads(first_arg_of_first_call)
        command = message['command']
        self.assertEqual('stopProviding', command)


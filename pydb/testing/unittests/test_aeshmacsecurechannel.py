import unittest
import pydb.com.securechannel.aeshmac_common
import pydb.com.jsonsession
import pydb.com.transport.tcpclient
import collections
import zlib
from mock import Mock, patch


from pydb.com.securechannel.aeshmacsecurechannel import AesHmacSecureChannel
used_module = 'pydb.com.securechannel.aeshmacsecurechannel'


class test_secure_channel_server_mode(unittest.TestCase):
    def setUp(self):
        self.upper_layer = Mock(spec=pydb.com.jsonsession.JsonSession)
        self.lower_layer = Mock(spec=pydb.com.transport.tcpclient.TcpClient)
        self.sc = AesHmacSecureChannel(self.upper_layer)
        self.sc.set_lower_layer(self.lower_layer)

        pydb.com.securechannel.aeshmac_common.get_nonce_512 = Mock()

    def test_empty(self):
        pass

    @patch(used_module+'.get_nonce_512')
    def test_accept_client_send_generated_nonce(self, mock_get_nonce):
        fake_nonce = "0" * 64
        mock_get_nonce.return_value = fake_nonce

        self.sc.transport_channel_established()
        self.lower_layer.send_message.assert_called_once_with(fake_nonce)

    def test_accept_client_no_friends_invalid_nonce(self):
        self.sc.transport_channel_established()
        self.assertRaises(Exception, self.sc.message_received, "a" * 64)


class test_secure_channel_client_mode(unittest.TestCase):
    def setUp(self):
        self.upper_layer = Mock(spec=pydb.com.jsonsession.JsonSession)
        self.lower_layer = Mock(spec=pydb.com.transport.tcpclient.TcpClient)
        self.sc = AesHmacSecureChannel(self.upper_layer)
        self.sc.set_lower_layer(self.lower_layer)

    def test_empty(self):
        pass

    def test_initiate_channel_does_not_fail(self):
        self.sc.initiate_secure_channel()


def disable_zlib(some_func):
    """ decorator to disable zlib """
    def inner(*args, **kwargs):
        old_c = zlib.compress
        old_d = zlib.decompress

        # noinspection PyUnusedLocal
        def no_compress(data, level):
            return data
        zlib.compress = no_compress
        zlib.decompress = lambda x: x

        some_func(*args, **kwargs)

        zlib.compress = old_c
        zlib.decompress = old_d
    return inner


class TestClientServerInteraction(unittest.TestCase):
    def setUp(self):
        self.messages_for_server = collections.deque()
        self.messages_for_client = collections.deque()

        self.client_sc = None
        self.server_sc = None

    def _deliver_message_for_server(self):
        if self.messages_for_server:
            self.server_sc.message_received(self.messages_for_server.pop())
            return True
        return False

    def _deliver_message_for_client(self):
        if self.messages_for_client:
            self.client_sc.message_received(self.messages_for_client.pop())
            return True
        return False

    def _setup_client(self, passphrase):
        self.client_upper_layer = Mock(spec=pydb.com.jsonsession.JsonSession)
        self.client_lower_layer = Mock(spec=pydb.com.transport.tcpclient.TcpClient)
        self.client_sc = AesHmacSecureChannel(self.client_upper_layer, passphrase)
        self.client_sc.set_lower_layer(self.client_lower_layer)

    def _setup_server(self, friends_list):
        self.server_upper_layer = Mock(spec=pydb.com.jsonsession.JsonSession)
        self.server_lower_layer = Mock(spec=pydb.com.transport.tcpclient.TcpClient)
        self.server_sc = AesHmacSecureChannel(self.server_upper_layer, friend_list=friends_list)
        self.server_sc.set_lower_layer(self.server_lower_layer)

    def _connect_client_and_server(self):
        def client_send_side_effect(message):
            self.messages_for_server.append(message)
        self.client_lower_layer.send_message.side_effect = client_send_side_effect

        def server_send_side_effect(message):
            self.messages_for_client.append(message)
        self.server_lower_layer.send_message.side_effect = server_send_side_effect

        self.client_sc.initiate_secure_channel()
        self.server_sc._accept_secure_channel()

    def test_empty(self):
        self._setup_client("a")
        self._setup_server(())
        self._connect_client_and_server()

    def test_key_exchange_no_friends(self):
        self._setup_client("a")
        self._setup_server(())

        self._connect_client_and_server()
        self.assertTrue(self._deliver_message_for_client())
        # the server should abort, as there is no friend with the given secret
        self.assertRaises(Exception, self._deliver_message_for_server)

    def test_key_exchange_correct_secret(self):
        self._setup_client("a")
        friend_id = 5
        friend_data = {'id': friend_id, 'name': 'a friend', 'comm_data': {'secret': 'a'}}

        self._setup_server([friend_data])
        self._connect_client_and_server()

        self.assertTrue(self._deliver_message_for_client())

        # the server should accept the client
        self.assertTrue(self._deliver_message_for_server())

        # should notify the upper level
        self.server_upper_layer.secure_channel_established.assert_called_once_with(friend_id)

        # and should answer
        self.assertTrue(self._deliver_message_for_client())

    def test_key_exchange_wrong_secret(self):
        self._setup_client("a")
        friend_data = {'id': 5, 'name': 'a friend', 'comm_data': {'secret': 'b'}}

        self._setup_server([friend_data])

        self._connect_client_and_server()
        self.client_sc.initiate_secure_channel()
        self.server_sc._accept_secure_channel()

        self.assertTrue(self._deliver_message_for_client())
        # the server should not accept the client
        self.assertRaises(Exception, self._deliver_message_for_server)

    @patch(used_module+'.get_nonce_512')
    def _setup_server_client_communcation_with_fake_nonce(self, fake_get_nonce):
        # fake the nonces so the key remains static
        fake_get_nonce.return_value = "0"*64

        self._setup_client("a")
        friend_id = 4
        friend_data = {'id': friend_id, 'name': 'a friend', 'comm_data': {'secret': 'a'}}

        self._setup_server([friend_data])
        self._connect_client_and_server()

        self.assertTrue(self._deliver_message_for_client())

        # the server should accept the client
        self.assertTrue(self._deliver_message_for_server())

        # should notify the upper level
        self.server_upper_layer.secure_channel_established.assert_called_once_with(friend_id)

        # and should answer
        self.assertTrue(self._deliver_message_for_client())

    @disable_zlib
    def test_known_ciphertext_for_aes(self):
        self._setup_server_client_communcation_with_fake_nonce()

        # send a message
        self.client_sc.send_message("a")

        # expect an encrypted message on the wire
        self.assertEquals(len(self.messages_for_server), 1)
        encrypted_maced_message = self.messages_for_server.pop()

        self.assertEqual(encrypted_maced_message.encode('hex'),
                         '54f13f72384dd414afcc39af91b5692ce8cf0d4a670a468b79b1d9b907e871249'
                         '05a8ca13dcae7c9b2751024fb32ce95f8888d53ae5780197e53a1566dc9999f2815')

        # now look at the server side decryption
        self.server_sc.message_received(encrypted_maced_message)

        # expect the decrypted message again
        self.server_upper_layer.message_received.assert_called_once_with("a")


if __name__ == '__main__':
    unittest.main()

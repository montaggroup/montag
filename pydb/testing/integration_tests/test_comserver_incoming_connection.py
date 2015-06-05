import unittest
import logging
import mock

logger = logging.getLogger('test_comserver_incoming_connection')

from pydb.com.securechannel import aeshmacsecurechannel
logging.basicConfig(level=logging.DEBUG)

def build_friend(id, name, add_secret=False, secret=None):
    friend_data = {
        'id': id,
        'name': name,
        'comm_data': {
            'type': 'tcp_aes',
            'hostname': 'a',
            'port': 5,
        }
    }

    if add_secret:
        friend_data['comm_data']['secret'] = secret

    return friend_data


def build_message(nonce_a, secret):
    message_first_64 = '0' * 64
    _, preshared_secret_kex_hmac = aeshmacsecurechannel.preshared_secrets_from_passphrase(secret)
    message_second_64 = aeshmacsecurechannel.calc_hmac(preshared_secret_kex_hmac, nonce_a + message_first_64)

    return message_first_64 + message_second_64


class TestComserverIncomingConnection(unittest.TestCase):
    def setUp(self):
        self.upper_layer_mock = mock.MagicMock()
        self.lower_layer_mock = mock.MagicMock()

        self.friend_id_good_secret = 4
        self.friend_id_bad_secret = 1000
        self.secret = '12345'

    def build_and_connect_secure_channel(self, friend_list):
        secure_channel = aeshmacsecurechannel.AesHmacSecureChannel(self.upper_layer_mock,
                                                                   pre_shared_secret_passphrase=None,
                                                                   friends=friend_list)
        secure_channel.set_lower_layer(self.lower_layer_mock)
        secure_channel.transport_channel_established()
        message = build_message(secure_channel.nonce_a, self.secret)
        secure_channel.message_received(message)

    def test_successful_connection_of_friend_with_secret_being_only_one_in_friends_list(self):
        friend_list = [
            build_friend(self.friend_id_good_secret, 'good friend', add_secret=True, secret=self.secret)
        ]

        self.build_and_connect_secure_channel(friend_list)
        self.upper_layer_mock.secure_channel_established.assert_called_once_with(self.friend_id_good_secret)

    def test_successful_connection_of_friend_with_secret_despite_another_friend_without_secret_in_friends_list(self):
        friend_list = [
            build_friend(self.friend_id_bad_secret, 'bad friend', add_secret=False),
            build_friend(self.friend_id_good_secret, 'good friend', add_secret=True, secret='12345')
        ]

        self.build_and_connect_secure_channel(friend_list)
        self.upper_layer_mock.secure_channel_established.assert_called_once_with(self.friend_id_good_secret)


if __name__ == '__main__':
    unittest.main()

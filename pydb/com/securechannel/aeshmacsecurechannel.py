import zlib
import pydb.crypto

import logging
from aeshmac_common import *

logger = logging.getLogger('secure_channel')

FLAG_COMPRESSED = 'C'
FLAG_UNCOMPRESSED = 'U'

# NOT YET EXTERNALLY REVIEWED FOR HIGH LEVEL SECURITY!
# secure channel using AES and HMAC-SHA-512
class AesHmacSecureChannel():
    def __init__(self, upper_layer, pre_shared_secret_passphrase=None, friend_list=()):
        self.upper_layer = upper_layer
        if pre_shared_secret_passphrase:
            self.preshared_secret_kex_cipher, self.preshared_secret_kex_hmac = preshared_secrets_from_passphrase(
                pre_shared_secret_passphrase)

        self.state = "not_initialized"
        self.role = "server"
        self.friend_list = list(friend_list)

        self.lower_layer = None
        self.nonce_a = None
        self.nonce_b = None
        self.session_secret_hmac = None
        self.auth_b = None
        self.session_cipher_incoming = None
        self.session_cipher_outgoing = None
        self.compression_level = 3

    def set_compression_level(self, compression_level):
        self.compression_level = compression_level

    def _change_state(self, new_state):
        # print "Changing state from "+self.state+" to "+new_state+"."
        self.state = new_state

    # needs to be called before any further function
    def set_lower_layer(self, lower_layer):
        self.lower_layer = lower_layer

    # to be called if we want to initiate the connection (client), no need for server code
    def initiate_secure_channel(self):
        self.role = "client"
        self._change_state("kex_waiting_on_nonceA")
        self.lower_layer.initiate_transport_channel()
        # entering key exchange passively, so do nothing until msg from server comes

    # to be called if we want to accept a connection (server), no need for client code
    def _accept_secure_channel(self):
        # entering key exchange, 1st msg from server to client
        self.nonce_a = get_nonce_512()
        self._change_state("kex_waiting_on_nonceB,authB")
        self.lower_layer.send_message(self.nonce_a)

    def send_message(self, message, skip_compression=False):
        if self.state != "established":
            raise RuntimeError("Trying to send message while not connected")

        # compress encrypt and mac
        if self.compression_level is None or skip_compression:
            compressed_message = FLAG_UNCOMPRESSED + message
        else:
            compressed_message = FLAG_COMPRESSED + zlib.compress(message, self.compression_level)
        #      print "Compressed message from %d to %d Bytes" % (len(message), len(compressed_message))
        #      if len(message) > 0:
        #        print "Ratio is %f%%" % ( len(compressed_message)*100/(len(message)) )
        msg_hmac = calc_hmac(self.session_secret_hmac, compressed_message)
        macd_msg = compressed_message + msg_hmac
        del compressed_message

        secure_msg = self.session_cipher_outgoing.encrypt(macd_msg)
        del macd_msg
        self.lower_layer.send_message(secure_msg)

    def lose_secure_channel(self, message):
        self.lower_layer.lose_transport_channel(message)

    def message_received(self, message):
        # print "messageReceived, len=%d: %s " %(len(message), message.encode("hex_codec")), self.state
        if self.state == "established":
            # decrypt/authenticate here
            macd_msg = self.session_cipher_incoming.decrypt(message)
            del message
            # print "decoded message:, len=%d: %s " %(len(macd_msg), macd_msg.encode("hex_codec"))

            message_payload = macd_msg[:-64]
            contained_hmac = macd_msg[-64:]
            del macd_msg

            calculated_hmac = calc_hmac(self.session_secret_hmac, message_payload)
            if calculated_hmac != contained_hmac:
                raise Exception("Message HMAC verification failed!")

            compression_flag = message_payload[0]
            if compression_flag == FLAG_UNCOMPRESSED:
                decompressed_message = message_payload[1:]
            else:
                decompressed_message = zlib.decompress(message_payload[1:])
                del message_payload
            self.upper_layer.message_received(decompressed_message)

        else:
            if self.role == "client":
                self._client_message_received(message)
            else:
                self._server_message_received(message)

    def transport_channel_established(self):
        self.lower_layer.set_max_data_length(KeyExchangeMaxMessageLength)
        if self.role == "server":
            self._accept_secure_channel()

    def transport_channel_failed(self, reason):
        self.upper_layer.secure_channel_failed(reason)

    def transport_channel_lost(self, reason):
        self.upper_layer.secure_channel_lost(reason)

    def _client_message_received(self, message):
        if self.state == "kex_waiting_on_nonceA":
            self.nonce_a = message
            self.nonce_b = get_nonce_512()
            self.auth_b = calc_hmac(self.preshared_secret_kex_hmac, self.nonce_a + self.nonce_b)
            self._change_state("kex_waiting_on_authA")
            self.lower_layer.send_message(self.nonce_b + self.auth_b)
        elif self.state == "kex_waiting_on_authA":
            auth = calc_hmac(self.preshared_secret_kex_hmac, self.nonce_a + self.nonce_b + self.auth_b)
            if auth != message:
                self._change_state("kex_failed_wrong_authA_received")
                raise Exception("kex_failed_wrong_authA_received")
            else:
                self._change_state("established")
                # disable message size limit
                self.lower_layer.set_max_data_length(0)
                self._derive_session_secret()
                self.upper_layer.secure_channel_established(friend_id=None)

    def _server_message_received(self, message):
        if self.state == "kex_waiting_on_nonceB,authB":
            # verify authenticator from client
            auth_found = False
            for friend in self.friend_list:

                (preshared_secret_kex_cipher, preshared_secret_kex_hmac) = preshared_secrets(friend)

                auth = calc_hmac(preshared_secret_kex_hmac, self.nonce_a + message[:64])
                if auth == message[64:]:
                    logger.info("Friend {} authenticated".format(friend["name"]))
                    self._change_state("established")
                    self.nonce_b = message[:64]
                    self.lower_layer.set_max_data_length(0)
                    self.preshared_secret_kex_cipher = preshared_secret_kex_cipher
                    self.preshared_secret_kex_hmac = preshared_secret_kex_hmac
                    self._derive_session_secret()
                    #generate authenticator for final kex message
                    auth_a = calc_hmac(self.preshared_secret_kex_hmac, self.nonce_a + message)
                    auth_found = True

                    self.lower_layer.send_message(auth_a)
                    self.upper_layer.secure_channel_established(friend['id'])
                    break

            if not auth_found:
                self._change_state("kex_failed_wrong_nonceB_received")
                raise Exception("kex_failed_wrong_nonceB_received")
        else:
            # execution should never reach this point
            assert False

    def _derive_session_secret(self):
        dkey_cipher = sha512d(self.preshared_secret_kex_cipher)[:32]
        dkey_hmac = sha512d(self.preshared_secret_kex_cipher)[32:]

        encrypted_nonces_cipher = pydb.crypto.AesCtr(dkey_cipher).encrypt(self.nonce_a + self.nonce_b)
        encrypted_nonces_hmac = pydb.crypto.AesCtr(dkey_hmac).encrypt(self.nonce_a + self.nonce_b)

        session_secret_cipher = sha512d(encrypted_nonces_cipher)
        session_secret_hmac = sha512d(encrypted_nonces_hmac)

        session_secret_cipher_outgoing = session_secret_cipher[32:]
        session_secret_cipher_incoming = session_secret_cipher[:32]

        if self.role == 'client':
            # switch secrets
            session_secret_cipher_outgoing, session_secret_cipher_incoming = \
                session_secret_cipher_incoming, session_secret_cipher_outgoing

        self.session_secret_hmac = session_secret_hmac[32:]

        self.session_cipher_outgoing = pydb.crypto.AesCtr(session_secret_cipher_outgoing)
        self.session_cipher_incoming = pydb.crypto.AesCtr(session_secret_cipher_incoming)

        logger.info("Established@%s session_cipher_secret: {}... ".format(
            self.role, session_secret_cipher.encode("hex_codec")[:4]))


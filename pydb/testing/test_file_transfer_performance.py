import unittest
import sys
import os

sys.path.append(os.getcwd())

import pydb.com.securechannel.aeshmacsecurechannel
import pydb.com.securechannel.insecurechannel
import pydb.com.transport.localloopbacktransportprotocol
import pydb.com.jsonsession
import pydb.com.json_and_binary_session
import pydb.com.session
from cStringIO import StringIO
import time
import logging
import mock

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("test_file_transfer_performance")

FILE_DELIVERY_REPETITIONS = 10

class TestFileTransferPerformance(unittest.TestCase):
    def setUp(self):
        script_path = os.path.dirname(__file__)
        self.test_file_contents = open(os.path.join(script_path, 'test_data', 'pg1661.epub'), "rb").read()
        self.file_stream = StringIO(self.test_file_contents)

        self.received_file_contents = ""
        def file_received(file_hash, extension, content, more_parts_follow):
            self.received_file_contents += content

        self.client_control = mock.MagicMock()
        self.client_control.command_deliver_file_received.side_effect = file_received

        self.server_control = mock.MagicMock()

    def _setup_loopback_transport(self, client_secure_channel, server_secure_channel):
        self.client_transport = pydb.com.transport.localloopbacktransportprotocol.LocalLoopBackTransportProtocol(
            client_secure_channel)
        self.server_transport = pydb.com.transport.localloopbacktransportprotocol.LocalLoopBackTransportProtocol(
            server_secure_channel)
        client_secure_channel.set_lower_layer(self.client_transport)
        server_secure_channel.set_lower_layer(self.server_transport)
        self.client_transport.set_partner(self.server_transport)
        self.server_transport.set_partner(self.client_transport)

    def _run_benchmark(self, secure_channel_name, client_secure_channel, server_session):
        client_secure_channel.initiate_secure_channel()
        start_wire_byte_count = self.server_transport.bytes_sent()
        start_time = time.clock()
        for i in xrange(FILE_DELIVERY_REPETITIONS):
            self.received_file_contents = ""
            pydb.com.session.send_chunked_file(server_session, 'epub', 'a_hash', self.file_stream)
            self.file_stream.seek(0)
        stop_time = time.clock()
        self.assertEqual(self.received_file_contents, self.test_file_contents)

        duration = stop_time - start_time
        if duration == 0:
            duration = 0.001
        payload_bandwidth_kbps = len(self.test_file_contents)  * FILE_DELIVERY_REPETITIONS / duration / 1024
        stop_wire_byte_count = self.server_transport.bytes_sent()

        bytes_sent_by_server = (stop_wire_byte_count-start_wire_byte_count) / FILE_DELIVERY_REPETITIONS
        overhead_bytes = bytes_sent_by_server-len(self.test_file_contents)

        print("Loopback results {:>60}: {:8} kbps, {:7.1f} ms, encoding overhead: {:7} bytes"
                    .format(secure_channel_name, int(payload_bandwidth_kbps), round(duration * 1000, 1),  overhead_bytes))

    def test_01_json_session_with_aeshmac_secure_channel(self):
        client_session = pydb.com.jsonsession.JsonSession(self.client_control)
        server_session = pydb.com.jsonsession.JsonSession(self.server_control)

        client_secure_channel = pydb.com.securechannel.aeshmacsecurechannel.AesHmacSecureChannel(
            client_session, pre_shared_secret_passphrase="hello")
        server_secure_channel = pydb.com.securechannel.aeshmacsecurechannel.AesHmacSecureChannel(
            server_session,
            friend_list=[
                {'name': 'test friend', 'id': 1, 'comm_data': {'secret': 'hello'}}
            ])

        client_session.set_lower_layer(client_secure_channel)
        server_session.set_lower_layer(server_secure_channel)

        self._setup_loopback_transport(client_secure_channel, server_secure_channel)

        self._run_benchmark('JsonSession with AesHmacSecureChannel', client_secure_channel, server_session)


    def test_02_json_session_with_insecure_channel(self):
        client_session = pydb.com.jsonsession.JsonSession(self.client_control)
        server_session = pydb.com.jsonsession.JsonSession(self.server_control)

        client_secure_channel = pydb.com.securechannel.insecurechannel.InsecureChannel(
            client_session)
        server_secure_channel = pydb.com.securechannel.insecurechannel.InsecureChannel(
            server_session)

        client_session.set_lower_layer(client_secure_channel)
        server_session.set_lower_layer(server_secure_channel)

        self._setup_loopback_transport(client_secure_channel, server_secure_channel)

        self._run_benchmark('JsonSession with InsecureChannel', client_secure_channel, server_session)

    def test_03_json_and_binary_session_with_aeshmac_secure_channel(self):
        client_session = pydb.com.json_and_binary_session.JsonAndBinarySession(self.client_control)
        server_session = pydb.com.json_and_binary_session.JsonAndBinarySession(self.server_control)

        client_secure_channel = pydb.com.securechannel.aeshmacsecurechannel.AesHmacSecureChannel(
            client_session, pre_shared_secret_passphrase="hello")
        server_secure_channel = pydb.com.securechannel.aeshmacsecurechannel.AesHmacSecureChannel(
            server_session,
            friend_list=[
                {'name': 'test friend', 'id': 1, 'comm_data': {'secret': 'hello'}}
            ])

        client_session.set_lower_layer(client_secure_channel)
        server_session.set_lower_layer(server_secure_channel)

        self._setup_loopback_transport(client_secure_channel, server_secure_channel)

        self._run_benchmark('JsonAndBinarySession with AesHmacSecureChannel', client_secure_channel, server_session)

    def test_04_json_and_binary_session_with_insecure_channel(self):
        client_session = pydb.com.json_and_binary_session.JsonAndBinarySession(self.client_control)
        server_session = pydb.com.json_and_binary_session.JsonAndBinarySession(self.server_control)

        client_secure_channel = pydb.com.securechannel.insecurechannel.InsecureChannel(
            client_session)
        server_secure_channel = pydb.com.securechannel.insecurechannel.InsecureChannel(
            server_session)

        client_session.set_lower_layer(client_secure_channel)
        server_session.set_lower_layer(server_secure_channel)

        self._setup_loopback_transport(client_secure_channel, server_secure_channel)

        self._run_benchmark('JsonAndBinarySession with InsecureChannel', client_secure_channel, server_session)

    def test_05_json_session_with_aeshmac_secure_channel_compression_level_0(self):
        client_session = pydb.com.jsonsession.JsonSession(self.client_control)
        server_session = pydb.com.jsonsession.JsonSession(self.server_control)

        client_secure_channel = pydb.com.securechannel.aeshmacsecurechannel.AesHmacSecureChannel(
            client_session, pre_shared_secret_passphrase="hello")
        client_secure_channel.set_compression_level(0)
        server_secure_channel = pydb.com.securechannel.aeshmacsecurechannel.AesHmacSecureChannel(
            server_session,
            friend_list=[
                {'name': 'test friend', 'id': 1, 'comm_data': {'secret': 'hello'}}
            ])
        server_secure_channel.set_compression_level(0)

        client_session.set_lower_layer(client_secure_channel)
        server_session.set_lower_layer(server_secure_channel)

        self._setup_loopback_transport(client_secure_channel, server_secure_channel)

        self._run_benchmark('JsonSession with AesHmacSecureChannel compress 0', client_secure_channel, server_session)

    def test_06_json_and_binary_session_with_aeshmac_secure_channel_compression_level_0(self):
        client_session = pydb.com.json_and_binary_session.JsonAndBinarySession(self.client_control)
        server_session = pydb.com.json_and_binary_session.JsonAndBinarySession(self.server_control)

        client_secure_channel = pydb.com.securechannel.aeshmacsecurechannel.AesHmacSecureChannel(
            client_session, pre_shared_secret_passphrase="hello")
        client_secure_channel.set_compression_level(0)

        server_secure_channel = pydb.com.securechannel.aeshmacsecurechannel.AesHmacSecureChannel(
            server_session,
            friend_list=[
                {'name': 'test friend', 'id': 1, 'comm_data': {'secret': 'hello'}}
            ])
        server_secure_channel.set_compression_level(0)


        client_session.set_lower_layer(client_secure_channel)
        server_session.set_lower_layer(server_secure_channel)

        self._setup_loopback_transport(client_secure_channel, server_secure_channel)

        self._run_benchmark('JsonAndBinarySession with AesHmacSecureChannel compress 0', client_secure_channel, server_session)

    def test_07_json_session_with_aeshmac_secure_channel_without_compression(self):
        client_session = pydb.com.jsonsession.JsonSession(self.client_control)
        server_session = pydb.com.jsonsession.JsonSession(self.server_control)

        client_secure_channel = pydb.com.securechannel.aeshmacsecurechannel.AesHmacSecureChannel(
            client_session, pre_shared_secret_passphrase="hello")
        client_secure_channel.set_compression_level(None)
        server_secure_channel = pydb.com.securechannel.aeshmacsecurechannel.AesHmacSecureChannel(
            server_session,
            friend_list=[
                {'name': 'test friend', 'id': 1, 'comm_data': {'secret': 'hello'}}
            ])
        server_secure_channel.set_compression_level(None)

        client_session.set_lower_layer(client_secure_channel)
        server_session.set_lower_layer(server_secure_channel)

        self._setup_loopback_transport(client_secure_channel, server_secure_channel)

        self._run_benchmark('JsonSession with AesHmacSecureChannel compress off', client_secure_channel, server_session)

    def test_08_json_and_binary_session_with_aeshmac_secure_channel_without_compression(self):
        client_session = pydb.com.json_and_binary_session.JsonAndBinarySession(self.client_control)
        server_session = pydb.com.json_and_binary_session.JsonAndBinarySession(self.server_control)

        client_secure_channel = pydb.com.securechannel.aeshmacsecurechannel.AesHmacSecureChannel(
            client_session, pre_shared_secret_passphrase="hello")
        client_secure_channel.set_compression_level(None)

        server_secure_channel = pydb.com.securechannel.aeshmacsecurechannel.AesHmacSecureChannel(
            server_session,
            friend_list=[
                {'name': 'test friend', 'id': 1, 'comm_data': {'secret': 'hello'}}
            ])
        server_secure_channel.set_compression_level(None)


        client_session.set_lower_layer(client_secure_channel)
        server_session.set_lower_layer(server_secure_channel)

        self._setup_loopback_transport(client_secure_channel, server_secure_channel)

        self._run_benchmark('JsonAndBinarySession with AesHmacSecureChannel compress off', client_secure_channel, server_session)
        
if __name__ == "__main__":
    unittest.main()
    
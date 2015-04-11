from twisted.internet.protocol import Factory
from twisted.internet.endpoints import TCP4ClientEndpoint
from tcptransportprotocol import build_tcp_transport_protocol
import logging

logger = logging.getLogger('tcpclient')


class TcpClient():
    def __init__(self, upper_layer, reactor_, target_host, target_port, comservice, target_bytes_per_second):
        self.upper_layer = upper_layer
        self.reactor = reactor_
        self.target_host = target_host
        self.target_port = target_port
        self.comservice = comservice
        self.target_bytes_per_second = target_bytes_per_second
        
        self.protocol = None
        self.max_data_length = 0

    def initiate_transport_channel(self):
        point = TCP4ClientEndpoint(self.reactor, self.target_host, self.target_port)

        client_factory = ProtocolFactory(self.upper_layer, self.comservice, self.target_bytes_per_second)
        d = point.connect(client_factory)
        d.addCallback(self.got_protocol)
        d.addErrback(self.handle_error)

    def send_message(self, msg):
        self.protocol.send_message(msg)

    def set_max_data_length(self, max_data_length):
        self.max_data_length = max_data_length
        if self.protocol:
            self.protocol.set_max_data_length(max_data_length)

    def lose_transport_channel(self, reason):
        self.protocol.lose_transport_channel(reason)

    def got_protocol(self, p):
        self.protocol = p
        self.protocol.set_max_data_length(self.max_data_length)

    def handle_error(self, error):
        logger.error("Got error: {}".format(error))
        self.upper_layer.transport_channel_failed(error)


class ProtocolFactory(Factory):
    def __init__(self, upper_layer, comservice, target_bytes_per_second):
        self.upper_layer = upper_layer
        self.comservice = comservice
        self.target_bytes_per_second = target_bytes_per_second

    # noinspection PyUnusedLocal
    def buildProtocol(self, address):
        host = address.host
        return build_tcp_transport_protocol(self.upper_layer, self.comservice, self.target_bytes_per_second,
                                            address.host)


import logging

logger = logging.getLogger("localllopbacktransportprotocol")

class LocalLoopBackTransportProtocol():
    """ used to emulate network transfer.
    """
    def __init__(self, upper_layer):
        self.upper_layer = upper_layer
        self.partner = None
        self.connected = False
        self._bytes_sent = 0

    def bytes_sent(self):
        return self._bytes_sent

    def set_partner(self, partner):
        self.partner = partner

    def initiate_transport_channel(self):
        assert(not self.connected)
        self.connected = True
        self.partner.connection_initiated()

    def connection_initiated(self):
        assert(not self.connected)
        self.connected = True
        self.upper_layer.transport_channel_established()


    def send_message(self, msg):
        assert(self.connected)
        self._bytes_sent += len(msg)
        self.partner.message_received(msg)

    def set_max_data_length(self, length):
        pass

    def lose_transport_channel(self, msg):
        logger.debug("LocalLoopBackTransportProtocol closing connection: {}".format(msg))
        self.partner.connectionLost('Connection closed by peer')

    def message_received(self, data=""):
        assert(self.connected)
        self.upper_layer.message_received(data)

    def connectionLost(self, reason):
        self.upper_layer.transport_channel_lost(reason)



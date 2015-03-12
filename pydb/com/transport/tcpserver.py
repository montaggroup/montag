from twisted.internet.protocol import Factory
from tcptransportprotocol import buildTcpTransportProtocol


class TcpServer(Factory):
    # the stack build function should build a complete protocol stack (without transport) and return the security layer
    def __init__(self, stack_build_function, comservice, upload_rate_limit_kbytes_per_second):
        self.stack_build_function = stack_build_function
        self.upload_rate_limit_kbytes_per_second = upload_rate_limit_kbytes_per_second
        self.comservice = comservice

    # noinspection PyUnusedLocal
    def buildProtocol(self, addr):
        upper_layer = self.stack_build_function()
        lowest_layer = buildTcpTransportProtocol(upper_layer, self.comservice,
                                                 self.upload_rate_limit_kbytes_per_second, addr.host)
        upper_layer.set_lower_layer(lowest_layer)
        return lowest_layer


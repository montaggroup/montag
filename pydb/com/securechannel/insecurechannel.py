# do not use this "secure" channel in production code!
class InsecureChannel():
    def __init__(self, upper_layer):
        self.upper_layer = upper_layer
        self.lower_layer = None

    # needs to be called before any further function
    def set_lower_layer(self, lower_layer):
        self.lower_layer = lower_layer

    # to be called if we want to initiate the connection (client), no need for server code
    def initiate_secure_channel(self):
        self.lower_layer.initiate_transport_channel()

    def send_message(self, message):
        self.lower_layer.send_message(message)

    def lose_secure_channel(self, message):
        self.lower_layer.lose_transport_channel(message)

    def message_received(self, message):
        self.upper_layer.message_received(message)

    def transport_channel_established(self):
        self.upper_layer.secure_channel_established(friend_id=None)

    def transport_channel_failed(self, reason):
        self.upper_layer.secure_channel_failed(reason)

    def transport_channel_lost(self, reason):
        self.upper_layer.secure_channel_lost(reason)


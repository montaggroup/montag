import logging
import re
from collections import deque

from twisted.internet import protocol
from twisted.internet import reactor as twisted_reactor

from ... import config

WaitingForLength = 0
WaitingForData = 1
Disconnected = 2

# This needs to be long enough so a slow client can insert 10000 entries without timing out the server
READ_TIMEOUT = 1200

# number of chunks to send at once (to allow throttling)
CHUNK_SIZE = 4096

# how long to wait between two calls of the job count getter
NUMBER_OF_JOBS_UPDATE_INTERVAL_SECONDS = 2

logger = logging.getLogger("tcptransportprotocol")

# how many bytes to buffer before trying to pause parent producers
MAXIMUM_QUEUE_SIZE_BYTES = 2 * 1024 * 1024


def memory_size():
    import gc
    import psutil
    import os

    gc.collect()
    rss = psutil.Process(os.getpid()).get_memory_info().rss
    return int(rss / 1024)


def memory_info(msg):
    if False:
        logger.info('{} {}'.format(msg, memory_size()))


def is_lan_address(host_address):
    # this helpful regex was taken from http://stackoverflow.com/a/28532296
    priv_lo = re.compile("^127\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
    priv_24 = re.compile("^10\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
    priv_20 = re.compile("^192\.168\.\d{1,3}.\d{1,3}$")
    priv_16 = re.compile("^172.(1[6-9]|2[0-9]|3[0-1]).[0-9]{1,3}.[0-9]{1,3}$")

    return priv_lo.match(host_address) or priv_24.match(host_address) or priv_20.match(host_address) or \
        priv_16.match(host_address)


def build_tcp_transport_protocol(upper_layer, com_server, target_bytes_per_second, host_address):
    if config.ignore_rate_limit_in_lan() and is_lan_address(host_address):
        logger.debug("Disabling rate limiting for host {} in LAN".format(host_address))
        target_bytes_per_second = 1000000000
    return TcpTransportProtocol(upper_layer, com_server, target_bytes_per_second, twisted_reactor)


class TcpTransportProtocol(protocol.Protocol, object):
    """
    note: some of the methods names here are not PEP8 as we are overwriting twisted methods
    """

    def __init__(self, upper_layer, comservice, target_bytes_per_second, reactor):
        self.upper_layer = upper_layer
        self.reactor = reactor
        self.data = bytearray()
        self.state = WaitingForLength
        self.expected_length = 0
        self.max_data_length = 0
        self.timeout = None

        self.paused = False

        self.queued_messages = deque([])
        self.chunks_to_transmit = deque([])
        self.delay_active = False

        self.comservice = comservice
        self.number_of_jobs_cache = 0

        self.update_number_of_jobs()

        self.target_bytes_per_second = target_bytes_per_second
        self.read_timeout = config.get_int_option('comserver', 'read_timeout_seconds', READ_TIMEOUT)
        self.upper_layer_paused = False

    def do_timeout(self):
        logger.warning("Timeout on network connection, closing.")
        self.lose_transport_channel("Read timeout")

    def current_number_of_jobs(self):
        return self.number_of_jobs_cache

    def update_number_of_jobs(self):
        if self.state != Disconnected:
            self.number_of_jobs_cache = self.comservice.get_number_of_running_jobs()
            self.reactor.callLater(NUMBER_OF_JOBS_UPDATE_INTERVAL_SECONDS, self.update_number_of_jobs)

    # noinspection PyPep8Naming
    def pauseProducing(self):
        self.paused = True
        logger.debug("Pause called, %s chunks and %s messages queued", len(self.chunks_to_transmit),
                     len(self.queued_messages))

    # noinspection PyPep8Naming
    def resumeProducing(self):
        logger.debug("Resume called, %s chunks and %s messages queued",
                     len(self.chunks_to_transmit), len(self.queued_messages))
        self.paused = False
        self._check_message_queue()
        self.dataReceived()

    # noinspection PyPep8Naming
    def stopProducing(self):
        logger.debug("Stop called")
        self.transport.loseConnection()

    def set_max_data_length(self, new_max_data_length):
        self.max_data_length = new_max_data_length

    def get_delay_after_chunk(self, chunk_size):
        return (chunk_size * 1.0 / self.target_bytes_per_second) * self.current_number_of_jobs()

    def _check_message_queue(self):
        if self.delay_active:
            return
        self.reactor.callLater(0, self._really_pump_message_queue)

    def message_queue_size(self):
        size = 0
        for el in self.chunks_to_transmit:
            size += len(el)

        for m in self.queued_messages:
            size += len(m)

        return size

    def _really_pump_message_queue(self):
        self.delay_active = False

        if not self.paused:
            if not self.chunks_to_transmit and self.queued_messages:
                next_message = self.queued_messages.popleft()
                self.chunks_to_transmit = package_and_split_message(next_message)

            if self.chunks_to_transmit:
                next_chunk = self.chunks_to_transmit.popleft()
                self.transport.write(next_chunk)
                chunk_delay = self.get_delay_after_chunk(len(next_chunk))

                self.delay_active = True
                self.reactor.callLater(chunk_delay, self._really_pump_message_queue)
        else:
            self.dataReceived()

        if self.message_queue_size() > MAXIMUM_QUEUE_SIZE_BYTES:
            if not self.upper_layer_paused:
                logger.debug("Pausing producers")
                self.upper_layer.pause_producing()
                self.upper_layer_paused = True
        else:
            if self.upper_layer_paused:
                logger.debug("Resuming producers")
                self.upper_layer.resume_producing()
                self.upper_layer_paused = False

            self.upper_layer.resume_producing()

    def send_message(self, msg):
        self.queued_messages.append(msg)
        self._check_message_queue()

    def lose_transport_channel(self, msg):
        logger.debug("TcpTransportProtocol closing connection: {}".format(msg))
        self.transport.loseConnection()

    def connectionMade(self):
        # register this class as a producer to allow the transport to tell us to pause
        self.transport.registerProducer(self, True)

        self.upper_layer.transport_channel_established()
        self.transport.bufferSize = 1024 * 1024 * 5

        self.timeout = self.reactor.callLater(self.read_timeout, self.do_timeout)

    def dataReceived(self, data=""):
        self.timeout.reset(self.read_timeout)
        self.data.extend(data)
        if self.max_data_length and len(self.data) > self.max_data_length:
            raise Exception("More than %d allowed bytes in incoming buffer (%d bytes), aborting connection" % (
                self.max_data_length, len(self.data)))

        if self.paused:
            return

        if self.state == WaitingForLength:
            if b"\n" in self.data:
                (length_text, remainder) = self.data.split(b"\n", 1)
                self.data = remainder

                try:
                    self.expected_length = int(length_text)
                    self.state = WaitingForData
                except ValueError:
                    logger.error("No valid int for length: {}".format(length_text))
                    self.transport.loseConnection()

        if self.state == WaitingForData:
            if len(self.data) >= self.expected_length:
                msg = self.data[0:self.expected_length]
                self.data = self.data[self.expected_length:]
                self.expected_length = 0
                self.state = WaitingForLength
                msg = str(msg)
                self.upper_layer.message_received(msg)
                self.reactor.callLater(0, self.dataReceived)

    def connectionLost(self, reason=protocol.connectionDone):
        self.state = Disconnected
        self.upper_layer.transport_channel_lost(reason)

def package_and_split_message(message):
    """ splits the message into evenly sized chunks and prepend message size header to first chunk """
    chunks = [message[i:i + CHUNK_SIZE] for i in range(0, len(message), CHUNK_SIZE)]
    len_info = "{}\n".format(len(message))
    chunks[0] = len_info + chunks[0]
    return deque(chunks)

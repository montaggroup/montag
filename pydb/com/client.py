from twisted.internet import reactor
from jsonsession import JsonSession
from json_and_binary_session import JsonAndBinarySession

import logging

logger = logging.getLogger("com.client")

from securechannel.aeshmacsecurechannel import AesHmacSecureChannel
from transport.tcpclient import TcpClient
import bulk_inserter
from .. import config

class ComClient():
    def __init__(self, main_db, friend_id, friend_comm_data, comservice):
        self._friend_id = friend_id
        self._friend_comm_data = friend_comm_data
        self.comservice = comservice

        self._communication_strategy = None
        self._main_db = main_db

        self._session = JsonAndBinarySession(self)
        self._secure_channel = AesHmacSecureChannel(self._session, self._friend_comm_data["secret"])
        self._session.set_lower_layer(self._secure_channel)
        
        self.target_bytes_per_second = config.upload_rate_limit_kbytes_per_second() * 1000

        self._tcp_client = None

    def connect_and_execute(self, communication_strategy):
        self._communication_strategy = communication_strategy

        self._tcp_client = TcpClient(self._secure_channel, reactor, self._friend_comm_data['hostname'],
                                     int(self._friend_comm_data['port']), self.comservice, self.target_bytes_per_second)
        self._secure_channel.set_lower_layer(self._tcp_client)
        self._session.initiate_session()

        # noinspection PyUnresolvedReferences
        reactor.run()

    def session_established(self, friend_id):
        assert (friend_id is None)
        inserter = bulk_inserter.BulkInserter(self._main_db, self._friend_id)

        self._communication_strategy.associated(self._session, self._friend_id, self.strategy_completed, inserter)

    def strategy_completed(self):
        self._session.set_upper_layer(self)

        def stop_all():
            self._session.lose_session("Completed")
            self._shutdown()

        # stop in a little while to allow the buffers to be flushed
        reactor.callLater(0.5, stop_all)

    # noinspection PyMethodMayBeStatic
    def _shutdown(self):
        # noinspection PyProtectedMember
        if not reactor._stopped:
            reactor.stop()

    def session_failed(self, reason):
        logger.error("sessionFailed: %s", reason)
        self._shutdown()

    def session_lost(self, reason):
        logger.error("The session was lost uncleanly: %s " % reason)
        self._shutdown()

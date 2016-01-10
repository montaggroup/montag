# coding=utf-8
import logging

from json_and_binary_session import JsonAndBinarySession
from transport.tcpserver import TcpServer
from securechannel.aeshmacsecurechannel import AesHmacSecureChannel
import master_strategy
import bulk_inserter
from .. import pyrosetup

logger = logging.getLogger("com.server")


class Server(object):
    def __init__(self, tcp_port_number, upload_rate_limit_kbps, reactor):
        self.db = pyrosetup.pydbserver()
        self.com_service = pyrosetup.comservice()
        self.file_server = pyrosetup.fileserver()

        if self.db.ping() != "pong":
            raise Exception("Unable to talk to pydb server, is it running?")

        tcp_server_factory = TcpServer(self.build_stack, self.com_service, upload_rate_limit_kbps * 1000)
        
        reactor.listenTCP(tcp_port_number, tcp_server_factory)
        logger.info("Server listening on port %s", tcp_port_number)

    def build_stack(self):

        sc = SessionController(self.db, self.com_service, self.file_server)
        session = JsonAndBinarySession(sc)
        sc.set_lower_layer(session)

        friends = self.db.get_friends()
        comm_data_store = pyrosetup.comm_data_store()
        for f in friends:
            f['comm_data'] = comm_data_store.get_comm_data(f['id'])
            
        secure_channel = AesHmacSecureChannel(session, friends=friends)
        session.set_lower_layer(secure_channel)

        return secure_channel


class SessionController(object):
    def __init__(self, main_db, com_service, file_server):
        self.job_id = None
        self.com_service = com_service
        self.file_server = file_server

        self._main_db = main_db
        self._communication_strategy = master_strategy.construct_master_server_strategy(self._main_db, self.com_service,
                                                                                        self.file_server)

        self._session = None

    def set_lower_layer(self, session):
        self._session = session

    def _register_job_with_comservice(self, friend_id):
        self.job_id = self.com_service.register_job("fetch_updates", friend_id)

    def _report_progress_to_comservice(self, current_phase_id, current_items_to_do, current_items_done):
        self.com_service.update_job_progress(self.job_id, current_phase_id, current_items_to_do, current_items_done)

    def session_established(self, friend_id):
        try:
            self._register_job_with_comservice(friend_id)
        except ValueError:
            self._session.lose_session("There is already a job running")
            return

        self._communication_strategy.set_progress_callback(self._report_progress_to_comservice)
        inserter = bulk_inserter.BulkInserter(self._main_db, friend_id)

        self._communication_strategy.associated(self._session, friend_id, self.strategy_completed, inserter)

    def _unregister_job(self):
        logging.info("Unregister job called, job is %s", self.job_id)
        if self.job_id is not None:
            self.com_service.unregister_job(self.job_id)
            self.job_id = None

    def strategy_completed(self):
        self._unregister_job()
        self._session.set_upper_layer(self)
        self._session.lose_session("Completed")

    def session_failed(self, reason):
        self._unregister_job()
        logger.error("sessionFailed: %s", reason)

    def session_lost(self, reason):
        self._unregister_job()
        logger.error("The session was lost uncleanly: %s ", reason)

    def pause_producing(self):
        pass

    def resume_producing(self):
        pass

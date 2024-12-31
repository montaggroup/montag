import json
import time
import logging
from .. import config

KEEP_ALIVE_SEND_INTERVAL_SECONDS = 120

logger = logging.getLogger('session')


class JsonAndBinarySession(object):
    def __init__(self, upper_layer):
        self.upper_layer = upper_layer
        self.lower_layer = None
        self._last_message_sent = 0
        self.expecting_content = None

    def set_upper_layer(self, upper_layer):
        self.upper_layer = upper_layer

    def set_lower_layer(self, lower_layer):
        self.lower_layer = lower_layer

    def initiate_session(self):
        self.lower_layer.initiate_secure_channel()

    def lose_session(self, reason):
        self.lower_layer.lose_secure_channel(reason)

    def get_database_entries(self, min_modification_date_authors, min_modification_date_tomes):
        msg = {'command': 'getDatabaseEntries', 'args': [min_modification_date_authors, min_modification_date_tomes]}
        self._send_message(msg)

    def set_number_documents(self, num_docs_in_batch, num_docs_total):
        self._send_message({'command': 'setNumberDocuments', 'args': [num_docs_in_batch, num_docs_total]})

    def deliver_document(self, document_type, doc):
        self._send_message({'command': 'deliverDocument', 'args': [document_type, doc]})

    def update_modification_dates(self, new_mod_date_authors, new_mod_date_tomes):
        self._send_message({'command': 'updateModificationDates', 'args': [new_mod_date_authors, new_mod_date_tomes]})

    def request_file(self, file_hash):
        self._send_message({'command': 'requestFile', 'args': [file_hash]})

    def deliver_file(self, file_hash, extension, content, more_parts_follow=False):
        has_content = bool(content)

        self._send_message({'command': 'deliverFile', 'args': [file_hash, extension, has_content, more_parts_follow]})
        if has_content:
            skip_compression = True
            if extension in ('txt', 'rtf'):
                skip_compression = False

            self.lower_layer.send_message(content, skip_compression=skip_compression)

    def request_stop_providing(self):
        self._send_message({'command': 'stopProviding', 'args': []})

    def _send_keep_alive(self):
        logger.info("Sending keepalive message to server")
        self._send_message({'command': 'noOp', 'args': []})

    def send_keep_alive_if_necessary(self):
        keep_alive_interval = config.get_int_option('comserver', 'keep_alive_send_interval_seconds',
                                                    KEEP_ALIVE_SEND_INTERVAL_SECONDS)
        if time.time() - self._last_message_sent > keep_alive_interval:
            self._send_keep_alive()

    def _send_message(self, object_to_send):
        self.lower_layer.send_message(json.dumps(object_to_send).encode('utf-8'))
        self._last_message_sent = time.time()

    def message_received(self, message):
        # print "Trying to decode message '%s'" %(message)
        if self.expecting_content is not None:
            (file_hash, extension, more_parts_follow) = self.expecting_content
            self.upper_layer.command_deliver_file_received(file_hash, extension, message, more_parts_follow)
            self.expecting_content = None
            return

        msg = json.loads(message)
        if 'command' not in msg:
            logger.error(u'No command in {}'.format(msg))
            self.lower_layer.lose_secure_channel('No command sent')

        del message
        command = msg['command']
        args = msg['args']

        if command == "getDatabaseEntries":
            min_modification_date_authors = args[0]
            min_modification_date_tomes = args[1]
            self.upper_layer.command_get_database_entries_received(min_modification_date_authors,
                                                                   min_modification_date_tomes)
        elif command == "setNumberDocuments":
            number_entries_batch = args[0]
            number_entries_total = args[1]
            self.upper_layer.command_set_number_documents_entries_received(number_entries_batch, number_entries_total)
        elif command == "deliverDocument":
            document_type = args[0]
            document = args[1]
            self.upper_layer.command_deliver_document_received(document_type, document)
        elif command == "updateModificationDates":
            new_mod_date_authors = args[0]
            new_mod_date_tomes = args[1]
            self.upper_layer.command_update_modification_date_received(new_mod_date_authors, new_mod_date_tomes)
        elif command == "requestFile":
            file_hash = args[0]
            self.upper_layer.command_request_file_received(file_hash)
        elif command == "deliverFile":
            file_hash = args[0]
            extension = args[1]
            has_content = args[2]
            more_parts_follow = args[3]
            del msg
            if has_content:
                self.expecting_content = (file_hash, extension, more_parts_follow)
            else:
                self.upper_layer.command_deliver_file_received(file_hash, extension, '', more_parts_follow)

        elif command == "stopProviding":
            self.upper_layer.command_stop_providing_received()
        elif command == "noOp":
            pass
        else:
            logger.error(u'Unsupported command "{}"'.format(command))
            self.lower_layer.lose_secure_channel("Unsupported command")

    def secure_channel_established(self, friend_id):
        self.upper_layer.session_established(friend_id)

    def secure_channel_failed(self, reason):
        self.upper_layer.session_failed(reason)

    def secure_channel_lost(self, reason):
        self.upper_layer.session_lost(reason)

    def pause_producing(self):
        self.upper_layer.pause_producing()

    def resume_producing(self):
        self.upper_layer.resume_producing()

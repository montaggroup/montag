# coding=utf-8
import logging

logger = logging.getLogger("com.metadata_requester")


class MetadataRequester(object):
    def __init__(self, main_db):
        self.main_db = main_db
        self._bulk_inserter = None

        self.min_modification_date_authors = None
        self.min_modification_date_tomes = None

        self.number_documents_to_receive_total = 0
        self.number_documents_received = 0

        self.document_progress_callback = None
        self._completion_callback = None
        self._failure_callback = None

        self._session = None
        self._friend_id = None

    def set_document_progress_callback(self, cb):
        """ sets a function that is called when progress in document downloading
        is made. The callback will receive two arguments: (items_to_do, items_done)
            If a value is unknown, -1 will be used """
        self.document_progress_callback = cb

    def activate(self, session, friend_id, completion_callback, failure_callback, bulk_inserter,
                 min_modification_date_authors, min_modification_date_tomes):
        self._session = session
        self._friend_id = friend_id
        session.set_upper_layer(self)
        self._completion_callback = completion_callback
        self._failure_callback = failure_callback
        self._bulk_inserter = bulk_inserter

        self._session.get_database_entries(min_modification_date_authors, min_modification_date_tomes)

    def command_set_number_documents_entries_received(self, number_entries_batch, number_entries_total):
        if self.number_documents_to_receive_total == 0:
            self.number_documents_to_receive_total = number_entries_total
        logger.info("Incoming entries: %s/%s", self.number_documents_received+number_entries_batch,
                    self.number_documents_to_receive_total)

        if number_entries_batch == 0 and self.number_documents_to_receive_total > 0:
            raise RuntimeError("Still {} documents outstanding but none sent"
                               .format(self.number_documents_to_receive_total))

        if self.document_progress_callback:
            self.document_progress_callback(self.number_documents_to_receive_total, self.number_documents_received)

    def command_deliver_document_received(self, document_type, document):
        self.number_documents_received += 1
        #    print "Got %d. document" % (self.documents_received)
        #    print document

        if document_type == "author":
            self._bulk_inserter.queue_author(document)
        elif document_type == "tome":
            self._bulk_inserter.queue_tome(document)
        else:
            logger.error("Unsupported document type: %s", document_type)
            self._abort_mission()

        self._session.send_keep_alive_if_necessary()
        if self.document_progress_callback:
            self.document_progress_callback(self.number_documents_to_receive_total, self.number_documents_received)

    def command_update_modification_date_received(self, new_mod_date_authors, new_mod_date_tomes):

        self._bulk_inserter.do_insert()

        logger.info("New mod dates: A %f T %f", new_mod_date_authors, new_mod_date_tomes)
        self.main_db.set_friend_last_query_dates(self._friend_id, new_mod_date_authors, new_mod_date_tomes)
        self.min_modification_date_authors = new_mod_date_authors
        self.min_modification_date_tomes = new_mod_date_tomes
        self._all_requests_completed()

    def _all_requests_completed(self):
        if self.number_documents_received < self.number_documents_to_receive_total > 0:
            self._session.get_database_entries(self.min_modification_date_authors, self.min_modification_date_tomes)
            return

        self._completion_callback()

    def _abort_mission(self):
        self._failure_callback()

    def session_failed(self, reason):
        logger.error("sessionFailed: %s", reason)
        self._abort_mission()

    def session_lost(self, reason):
        logger.error("The session was lost uncleanly: %s ", reason)
        self._abort_mission()

    def pause_producing(self):
        pass

    def resume_producing(self):
        pass

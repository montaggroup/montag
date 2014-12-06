import os
from twisted.internet import defer
from twisted.internet import reactor
from twisted.internet.task import deferLater
import logging
import session

logger = logging.getLogger("com.provider")


def deferred_wait(time_in_seconds):
    return deferLater(reactor, time_in_seconds, lambda: None)


class Provider():
    def __init__(self, db):
        self.db = db
        self.lower_layer = None
        self._completion_callback = None
        self._failure_callback = None
        self.providing_progress_callback = None
        self.number_documents_sent = 0
        self.number_files_sent = 0

    def activate(self, session_layer, completion_callback, failure_callback):
        self.lower_layer = session_layer
        session_layer.set_upper_layer(self)
        self._completion_callback = completion_callback
        self._failure_callback = failure_callback

    def command_stop_providing_received(self):
        self._completion_callback()

    def set_providing_progress_callback(self, cb):
        """ sets a function that is called when progress in uploading
        is made. The callback will receive two arguments: (documents_provided, files_provided)
            If a value is unknown, -1 will be used """
        self.providing_progress_callback = cb

    @defer.inlineCallbacks
    def command_get_database_entries_received(self, min_modification_date_authors, min_modification_date_tomes):

        (changed_author_guids, changed_tome_guids, new_min_modification_date_authors,
         new_min_modification_date_tomes) = self.db.get_document_change_package(min_modification_date_authors,
                                                                                min_modification_date_tomes)

        total_changed_authors, total_changed_tomes = self.db.changed_documents_count(min_modification_date_authors,
                                                                                     min_modification_date_tomes)

        logger.debug("Database entries requested: Authors {}, Tomes {}".format(
            min_modification_date_authors, min_modification_date_tomes))

        num_docs = len(changed_author_guids) + len(changed_tome_guids)
        num_docs_total = total_changed_authors + total_changed_tomes
        self.lower_layer.set_number_documents(num_docs, num_docs_total)

        for author_guid in changed_author_guids:
            # print "Fetching for "y,author_id
            author = self.db.get_author_document_by_guid(author_guid)
            # print "Author %d data: %s" %(author_id, author)
            self.lower_layer.deliver_document("author", author)
            self._progress_made(number_documents_increment=1)
            yield deferred_wait(0)

        for tome_guid in changed_tome_guids:
            tome = self.db.get_tome_document_by_guid(tome_guid)
            self.lower_layer.deliver_document("tome", tome)
            self._progress_made(number_documents_increment=1)
            yield deferred_wait(0)

        logger.debug("Sent documents up to Authors {}, Tomes {}".format(
                     new_min_modification_date_authors, new_min_modification_date_tomes))
        self.lower_layer.update_modification_dates(new_min_modification_date_authors, new_min_modification_date_tomes)

    def command_request_file_received(self, file_hash):
        logger.debug("Request for file {} received".format(file_hash))
        local_path = self.db.get_local_file_path(file_hash)

        if not local_path:
            logger.info("Sending negative reply for hash %s" % file_hash)
            self.lower_layer.deliver_file(file_hash, extension="", content="", more_parts_follow=False)
            return

        extension_with_dot = os.path.splitext(local_path)[1]
        extension = extension_with_dot[1:]

        with open(local_path, 'rb') as fp:
            session.send_chunked_file(self.lower_layer, extension, file_hash, fp)
            self._progress_made(number_files_increment=1)

    def _progress_made(self, number_documents_increment=0, number_files_increment=0):
        self.number_documents_sent += number_documents_increment
        self.number_files_sent += number_files_increment
        if self.providing_progress_callback is not None:
            self.providing_progress_callback(self.number_documents_sent, self.number_files_sent)

    # noinspection PyMethodMayBeStatic
    def session_established(self):
        logger.debug("New Session for server")

    # noinspection PyMethodMayBeStatic
    def session_failed(self, reason):
        logger.info("Session failed: {}".format(reason))

    # noinspection PyMethodMayBeStatic
    def session_lost(self, reason):
        logger.info("Client disconnected, reason: {}".format(reason))
        self._failure_callback()


default_queue_limit = 1000


class BulkInserter(object):
    def __init__(self, main_db, friend_id):
        self.main_db = main_db
        self.friend_id = friend_id
        self._tome_documents = []
        self._author_documents = []
        self.queue_limit = default_queue_limit

    def queue_tome(self, tome_document):
        self._tome_documents.append(tome_document)

        if len(self._tome_documents) > self.queue_limit:
            self.do_insert()

    def queue_author(self, author_document):
        self._author_documents.append(author_document)

        if len(self._author_documents) > self.queue_limit:
            self.do_insert()

    def do_insert(self):
        """ Flushes the internal queues and actually inserts into the database
        """
        if self._author_documents:
            self.main_db.load_author_documents_from_friend(self.friend_id, self._author_documents)
            self._author_documents = []

        if self._tome_documents:
            self.main_db.load_tome_documents_from_friend(self.friend_id, self._tome_documents)
            self._tome_documents = []

    def set_queue_limit(self, queue_limit):
        self.queue_limit = queue_limit

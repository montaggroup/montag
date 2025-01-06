import Pyro4

from pydb import whooshindex
from pydb import indexthread
import os
import logging

import Pyro4

logger = logging.getLogger('indexserver')


def build(db_dir, schema_dir):
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)

    index_thread = indexthread.build(db_dir, schema_dir)
    whoosh_index = whooshindex.build(db_dir)
    return IndexServer(whoosh_index, index_thread)

@Pyro4.expose
class IndexServer(object):
    def __init__(self,  whoosh_index, index_thread):
        self.whoosh_index = whoosh_index
        self.index_thread = index_thread

    def start(self):
        self.index_thread.start()

    def stop(self):
        logger.info("Requesting stop")
        self.index_thread.request_stop()

    def search_tomes(self, query):
        tome_guids = self.whoosh_index.search_tomes(query)
        return tome_guids

    def update_index(self):
        self.index_thread.request_index_update()

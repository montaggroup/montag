import whooshindex
import indexthread
import os


class IndexServer():

    def __init__(self, base_path):
        db_dir = os.path.join(base_path, "db")
        if not os.path.exists(db_dir):
            os.mkdir(db_dir)

        schema_path = os.path.join(base_path, "db-schemas")

        self.whoosh_index = whooshindex.WhooshIndex(db_dir)

        progress_file_name = os.path.join(db_dir, "whoosh_progress.txt")
        progress_file = indexthread.ProgressFile(progress_file_name)
        self.index_thread = indexthread.IndexThread(schema_path, db_dir, progress_file)
        self.index_thread.start()

    def stop(self):
        print "Requesting stop"
        self.index_thread.request_stop()

    def search_tomes(self, query):
        tome_guids = self.whoosh_index.search_tomes(query)
        return tome_guids

    def update_index(self):
        self.index_thread.request_index_update()

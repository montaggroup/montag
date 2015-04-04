import multiprocessing
import logging
import pydb.pyrosetup

logger = logging.getLogger("com.background_file_inserter")


class BackgroundFileInserter():
    def __init__(self):
        self.insert_process = None

    def wait_for_insert_to_complete(self):
        if self.insert_process is None:
            return

        if self.insert_process.is_alive():
            logger.debug("Insert process still alive, waiting for process end")
            self.insert_process.join()
        self.insert_process = None
        logger.debug("No more file inserts running")

    def insert_file_in_background(self, completed_file_name, extension, file_hash):
        logger.debug("About to insert {} in background, checking whether previous insert is complete".format(file_hash))
        self.wait_for_insert_to_complete()

        def insert_it():
            logger.debug("Inserting {} in background".format(file_hash))
            file_server = pydb.pyrosetup.fileserver()
            file_server.add_file_from_local_disk(completed_file_name, extension,
                                                 only_allowed_hash=file_hash, move_file=True)

            com_service = pydb.pyrosetup.comservice()
            com_service.release_file_after_fetching(file_hash, success=True)
            logger.debug("Background insert complete")

        self.insert_process = multiprocessing.Process(target=insert_it)
        self.insert_process.start()

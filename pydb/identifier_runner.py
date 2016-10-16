# coding=utf-8
import os
import Queue

import identifiers.montag_lookup
import pydb.pyrosetup
import network_params
import logging
import importerdb

logger = logging.getLogger(__name__)


def db_path(db_dir, db_name):
    return os.path.join(db_dir, db_name + ".db")


def build_identifier_runner(db_dir, schema_dir):
    importer_db_path = db_path(db_dir, 'importer')

    pydb_ = pydb.pyrosetup.pydbserver()
    identifiers_to_use = [
        identifiers.montag_lookup.MontagLookupByHash(pydb_)
    ]

    importer_db = importerdb.ImporterDB(importer_db_path, schema_dir=schema_dir)
    return IdentifierRunner(pydb_, identifiers_to_use, importer_db)


class IdentifierRunner(object):
    def __init__(self, pydb_, identifiers_to_use, importer_db):
        self.notification_queue = None
        self.pydb = pydb_
        self.identifiers_to_use = identifiers_to_use
        self.importer_db = importer_db
        self.stop_requested = False

    def _try_file(self, file_info):
        hash_ = file_info['hash']
        self.importer_db.set_file_input_state(hash_, importerdb.STATE_PROCESSING)
        file_facts = self.importer_db.get_facts(hash_)
        logger.debug('Trying to identify file %s', hash_)

        self.importer_db.begin()

        best_identification_fidelity = 0
        best_identification_document = None

        for identifier in self.identifiers_to_use:
            identifier_name = identifier.__class__.__name__
            logger.debug('Trying identifier %s on file %s', identifier_name, hash_)

            run_info_key = identifier_name + '_ran'

            if run_info_key in file_facts and file_facts[run_info_key] == 1:
                logger.debug('Identifier %s already ran on %s, skipping', identifier_name, hash_)
                continue

            try:
                results = identifier.identify(file_info, file_facts)
            except Exception as e:
                logger.exception('Error running identifier %s on file %s: %s',identifier_name, hash_, e.message)
                continue
            for r in results:
                self.importer_db.add_identifier_result(
                    hash_,
                    identifier_name,
                    r['fidelity'],
                    r['document']
                )

                if r['fidelity'] > best_identification_fidelity:
                    best_identification_fidelity = r['fidelity']
                    best_identification_document = r['document']

            self.importer_db.add_fact(hash_, run_info_key, '1')

        if best_identification_fidelity >= network_params.Min_Relevant_Fidelity:
            self.import_identification_document(best_identification_document, hash_)
            self.importer_db.set_file_input_state(hash_, importerdb.STATE_IDENTIFIED)
        elif best_identification_fidelity > 0:
            self.importer_db.set_file_input_state(hash_, importerdb.STATE_UNCERTAIN)
        else:
            self.importer_db.set_file_input_state(hash_, importerdb.STATE_UNIDENTIFIED)
        self.importer_db.commit()

    def run_on_all_unprocessed_files(self):
        file_infos = self.importer_db.get_files_by_state(importerdb.STATE_UNPROCESSED)
        if len(file_infos) > 0:
            logger.info('%s files to process', len(file_infos))
        for file_info in file_infos:
            self._try_file(file_info)
            if self.stop_requested:
                return

    def _clear_partially_processed_files(self):
        self.importer_db.begin()
        processing_files = self.importer_db.get_files_by_state(importerdb.STATE_PROCESSING)
        for f in processing_files:
            logger.warn("Files %s was in processing state, resetting", f['hash'])
            self.importer_db.set_file_input_state(f['hash'], importerdb.STATE_UNPROCESSED)
        self.importer_db.commit()

    def process_queue_forever(self, notification_queue):
        def clear_queue(q):
            try:
                while True:
                    q.get(False, 0)
            except Queue.Empty:
                pass

        self.notification_queue = notification_queue
        self._clear_partially_processed_files()

        while not self.stop_requested:
            self.run_on_all_unprocessed_files()
            notification_queue.get()
            # remove all other pending items, we'll do all at once
            clear_queue(notification_queue)

    def request_stop(self):
        logger.info("Requesting stop of identifier runner")
        self.stop_requested = True
        if self.notification_queue is not None:
            self.notification_queue.put(None)

    def import_identification_document(self, document, hash_):
        if 'guid' in document \
                and 'file_already_added_with_correct_fidelity' in document \
                and document['file_already_added_with_correct_fidelity']:
            # shortcut: we already know that the file is added with the correct fidelity
            return
        else:
            raise RuntimeError("Import of documents not yet implemented")



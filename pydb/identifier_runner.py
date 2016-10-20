# coding=utf-8
import os
import Queue
import logging

import identifiers.montag_lookup
import pydb.pyrosetup
import pydb
import pydb.config
import network_params
import importerdb

logger = logging.getLogger(__name__)


def db_path(db_dir, db_name):
    return os.path.join(db_dir, db_name + ".db")


def build_identifier_runner(db_dir, schema_dir, identifiers_to_use=None):
    importer_db_path = db_path(db_dir, 'importer')

    pydb_ = pydb.pyrosetup.pydbserver()
    if identifiers_to_use is None:
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

            if run_info_key in file_facts and file_facts[run_info_key] == '1':
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

            self.importer_db.insert_or_replace_fact(hash_, run_info_key, '1')

        if best_identification_fidelity >= network_params.Min_Relevant_Fidelity:

            if self.import_filter_accepts_document(best_identification_document):
                guid = self.import_identification_document(best_identification_document, hash_,
                                                    file_facts['file_size'], file_facts['file_extension'])
                self.importer_db.insert_or_replace_fact(hash_, 'result_tome_guid', guid)
                self.importer_db.set_file_input_state(hash_, importerdb.STATE_IDENTIFIED)
            else:
                logger.info('File {} was identified successfully, but import filter rejected it'.format(hash_))
                self.importer_db.set_file_input_state(hash_, importerdb.STATE_REJECTED)
                # file store contents are removed through file store maintenance
        elif best_identification_fidelity > 0:
            self.importer_db.set_file_input_state(hash_, importerdb.STATE_UNCERTAIN)
        else:
            self.importer_db.set_file_input_state(hash_, importerdb.STATE_UNIDENTIFIED)
        self.importer_db.commit()

    def _run_on_file_infos(self, file_infos):
        if len(file_infos) > 0:
            logger.info('%s files to process', len(file_infos))
        for file_info in file_infos:
            self._try_file(file_info)
            if self.stop_requested:
                return

    def run_on_all_unprocessed_files(self):
        file_infos = self.importer_db.get_files_by_state(importerdb.STATE_UNPROCESSED)
        self._run_on_file_infos(file_infos)

    def run_on_all_pending_files(self):
        file_infos = self.importer_db.get_files_by_state(importerdb.STATE_UNPROCESSED) + \
        self.importer_db.get_files_by_state(importerdb.STATE_UNIDENTIFIED) + \
        self.importer_db.get_files_by_state(importerdb.STATE_UNCERTAIN)
        self._run_on_file_infos(file_infos)

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

    def import_identification_document(self, doc, hash_, file_size, file_extension):
        if 'guid' in doc \
                and 'file_already_added_with_correct_fidelity' in doc \
                and doc['file_already_added_with_correct_fidelity']:
            # shortcut: we already know that the file is added with the correct fidelity
            return doc['guid']
        else:  # we have a document with tome information and one or more authors
            author_docs = doc['authors']
            if not author_docs:
                logger.error('Document did not contain author info: {}'.format(doc))
                return
            author_names = [a['name'] for a in author_docs]
            author_ids = self.pydb.find_or_create_authors(author_names, fidelity=author_docs[0]['fidelity'])

            tag_values = [t['tag_value'] for t in doc['tags']]

            language = doc['principal_language']

            tome_id = self.pydb.find_or_create_tome(doc['title'], language,
                                                    author_ids, doc['subtitle'], tome_type=doc['tome_type'],
                                                    fidelity=doc['fidelity'], edition=doc['edition'],
                                                    publication_year=doc['publication_year'],
                                                    tags_values=tag_values)

            self.pydb.link_tome_to_file(tome_id, hash_, file_size, file_extension=file_extension,
                                        file_type=pydb.FileType.Content, fidelity=doc['fidelity'])

            tome = self.pydb.get_tome(tome_id)
            return tome['guid']

            # @todo refactor and move to server together with code from pydb add: pydb.import_tome(tome_import_document)
            # @todo synopsis support

    def import_filter_accepts_document(self, best_identification_document):
        if 'guid' in best_identification_document \
                and 'file_already_added_with_correct_fidelity' in best_identification_document \
                and best_identification_document['file_already_added_with_correct_fidelity']:
            # no need/possibility to filter
            return True

        tome_language = best_identification_document['principal_language']
        if tome_language is None:
            return pydb.config.accept_unknown_languages()

        filter_languages = pydb.config.filter_tome_languages()
        if not filter_languages:
            return True
        return tome_language.lower() in filter_languages




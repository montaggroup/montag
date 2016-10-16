# coding=utf-8
import sqlite3 as sqlite
import logging
import sqlitedb
import time
import json

logger = logging.getLogger(__name__)

STATE_UNPROCESSED = 'Unprocessed'
STATE_PROCESSING = 'Processing'
STATE_UNIDENTIFIED = 'Unidentified'
STATE_UNCERTAIN = 'Uncertain'
STATE_IDENTIFIED = 'Identified'
STATE_REJECTED = 'Rejected'

states = [STATE_UNPROCESSED, STATE_PROCESSING, STATE_UNIDENTIFIED, STATE_IDENTIFIED, STATE_UNCERTAIN, STATE_REJECTED]


class ImporterDB(sqlitedb.SqliteDB):
    def __init__(self, db_file_path, schema_dir):

        sqlitedb.SqliteDB.__init__(self, db_file_path, schema_dir)

        try:
            logger.debug('Loading schema')
            self._execute_sql_file('db-schema-importer.sql')
            logger.debug('Done loading schemas')
        except sqlite.IntegrityError as e:
            logger.info(u'Before rollback due to {}'.format(e))
            self.rollback()
            pass

        self._update_schema_if_necessary()
        logger.info('Importer DB initialized')

    def _update_schema_if_necessary(self):
        pass

    def add_file(self, file_hash):
        self.insert_object('identifier_files', {'hash': file_hash,
                                                'input_state': STATE_UNPROCESSED,
                                                'date_import': time.time(),
                                                'date_last_state_change': time.time()})

    def set_file_input_state(self, file_hash, input_state):
        self.update_object('identifier_files', {'hash': file_hash}, {'input_state': input_state,
                                                                     'date_last_state_change': time.time()})

    def is_file_known(self, file_hash):
        number_entries = self.count_rows('identifier_files', 'hash=?', [file_hash])
        return number_entries > 0

    def get_file_info(self, file_hash):
        result = self.get_list_of_objects('SELECT * FROM identifier_files WHERE hash=?', [file_hash])
        if result:
            return result[0]

    def get_file_count_by_state(self, state):
        return self.get_single_value('SELECT COUNT(*) from identifier_files WHERE input_state=?', [state])

    def get_files_by_state(self, state):
        return self.get_list_of_objects('SELECT * FROM identifier_files WHERE input_state=?', [state])

    def get_pending_files(self):
        return self.get_list_of_objects('SELECT * FROM identifier_files WHERE input_state!=?', [STATE_IDENTIFIED])

    def get_recently_identified_files(self):
        return self.get_list_of_objects('SELECT * FROM identifier_files WHERE input_state=? ORDER BY date_last_state_change DESC LIMIT 100', [STATE_IDENTIFIED])

    def add_fact(self, hash_, key, value):
        return self.insert_object('identifier_facts', {'hash': hash_, 'key': key, 'value': value})

    def insert_or_replace_fact(self, hash_, key, value):
        return self.insert_object('identifier_facts', {'hash': hash_, 'key': key, 'value': value}, allow_replace=True)

    def remove_fact(self, hash_, key):
        self.cur.execute('DELETE FROM identifier_facts WHERE hash=? AND key=?', [hash_, key])

    def get_fact_value(self, hash_, key):
        results = self.get_list_of_objects('SELECT * FROM identifier_facts WHERE hash=? AND `key`=?', [hash_, key])
        if not results:
            return None
        return results[0]['value']

    def get_facts(self, hash_):
        all_facts = self.get_list_of_objects('SELECT * FROM identifier_facts WHERE hash=?', [hash_])
        return {fact['key']: fact['value'] for fact in all_facts}

    def get_identifier_results(self, hash_):
        return self.get_list_of_objects('SELECT * FROM identifier_results WHERE hash=?', [hash_])

    def add_identifier_result(self, hash_, identifier_name, fidelity, result):
        self.insert_object('identifier_results', {
            'hash': hash_,
            'identifier_name': identifier_name,
            'fidelity': fidelity,
            'tome_document': json.dumps(result)})


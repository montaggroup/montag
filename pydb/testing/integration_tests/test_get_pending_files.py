# coding=utf-8
import unittest
import logging

import pydb
import pydb.testing
from pydb.testing.integration_tests import helpers

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARN)


class TestGetPendingFiles(unittest.TestCase):
    def setUp(self):
        self.main_db = helpers.build_main_db_memory_only(pydb.testing.guess_schema_dir())
        self.importer_db = self.main_db.importer_db
        self.local_db = self.main_db.local_db

    def test_get_pending_files_returns_empty_result_if_no_entries_in_db(self):
        result = self.main_db.get_import_pending_files()
        self.assertFalse(result)

    def test_get_pending_files_does_not_crash_if_only_pending_files_entry_exists(self):
        self.importer_db.add_file('a_hash')
        result = self.main_db.get_import_pending_files()
        self.assertEqual(len(result), 1)
        entry = result[0]

    def test_get_pending_files_returns_correct_result_if_one_entry_in_db(self):
        self.importer_db.add_file('a_hash')
        self.local_db.add_local_file('a_hash', 'epub')
        self.importer_db.add_fact('a_hash', 'file_name', 'some.epub')

        result = self.main_db.get_import_pending_files()
        self.assertEqual(len(result), 1)
        entry = result[0]
        self.assertEqual(entry['hash'], 'a_hash')
        self.assertEqual(entry['file_extension'], 'epub')
        self.assertEqual(entry['file_name'], 'some.epub')


if __name__ == '__main__':
    unittest.main()

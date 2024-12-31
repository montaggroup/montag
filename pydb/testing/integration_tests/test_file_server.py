import unittest
import os
import time
import tempfile
import logging

import pydb.fileserver
import pydb.maindb
import pydb.testing
from pydb.testing.test_data import get_book_path

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("test_file_server")


class TestFileServer(unittest.TestCase):
    def setUp(self):
        pydb_base_dir = tempfile.mkdtemp('test_file_server')
        pydbserver = pydb.maindb.build(os.path.join(pydb_base_dir, 'db'),
                                       pydb.testing.guess_schema_dir())

        self.file_server = pydb.fileserver.build(os.path.join(pydb_base_dir, 'filestore'), pydbserver)
        print("filestore is in ", os.path.join(pydb_base_dir, 'filestore'))
        time.sleep(0.5)

        self.test_epub_path = get_book_path('pg1661.epub')
        self.test_txt_path = get_book_path('pg1661.txt')

    def test_file_is_not_in_store_if_not_added_before(self):
        self.assertFalse(self.file_server.is_file_in_store(self.test_epub_path, 'epub'))
        self.assertFalse(self.file_server.is_file_in_store(self.test_txt_path, 'txt'))

    def test_file_is_in_store_after_it_has_been_added(self):
        self.file_server.add_file_from_local_disk(self.test_epub_path, 'epub')
        self.assertTrue(self.file_server.is_file_in_store(self.test_epub_path, 'epub'))
        self.assertFalse(self.file_server.is_file_in_store(self.test_txt_path, 'txt'))

    def test_restrip_with_file_not_existing_leads_to_ioerror(self):
        with self.assertRaises(IOError):
            self.file_server.re_strip_file('1234567812345678123456781234567812345678123456781234567812345678', 'epub')

    def test_restrip_without_change_does_not_crash(self):
        local_file_id, file_hash, size = self.file_server.add_file_from_local_disk(self.test_epub_path, 'epub')
        self.file_server.re_strip_file(file_hash, 'epub')

    def test_after_delete_a_file_is_not_in_the_store_anymore(self):
        local_file_id, file_hash, size = self.file_server.add_file_from_local_disk(self.test_epub_path, 'epub')
        self.assertTrue(self.file_server.is_file_in_store(self.test_epub_path, 'epub'))

        self.file_server.delete_file(file_hash)
        self.assertFalse(self.file_server.is_file_in_store(self.test_epub_path, 'epub'))

    def test_after_re_adding_an_existing_file_without_extension_no_new_entry_is_created(self):
        txt_file_without_extension = get_book_path('pg1661_txt')
        first_id, first_hash, first_size = self.file_server.add_file_from_local_disk(self.test_txt_path, 'txt')
        second_id,  second_hash, second_size = self.file_server.add_file_from_local_disk(txt_file_without_extension, '')
        self.assertEqual(first_id, second_id)


if __name__ == "__main__":
    unittest.main()


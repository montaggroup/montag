import unittest
import sys
import os
import time
import tempfile

sys.path.append(os.getcwd())

import pydb.fileserver
import pydb.maindb

import logging

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("test_file_server")


class TestFileServer(unittest.TestCase):
    def setUp(self):
        script_path = os.path.dirname(__file__)

        pydb_base_dir = tempfile.mkdtemp('test_file_server')
        pydbserver = pydb.maindb.build(os.path.join(pydb_base_dir, 'db'),
                                       os.path.join(script_path, '..', '..', 'db-schemas'))

        self.file_server = pydb.fileserver.build(os.path.join(pydb_base_dir, 'filestore'), pydbserver)
        print "filestore is in ", os.path.join(pydb_base_dir, 'filestore')
        # @todo wait for ping ready instead of fixed time
        time.sleep(0.5)

        self.test_epub_path = os.path.join(script_path, 'test_data', 'pg1661.epub')
        self.test_txt_path = os.path.join(script_path, 'test_data', 'pg1661.txt')

    def test_file_is_not_in_store_if_not_added_before(self):
        self.assertFalse(self.file_server.is_file_in_store(self.test_epub_path, 'epub'))
        self.assertFalse(self.file_server.is_file_in_store(self.test_txt_path, 'txt'))

    def test_file_is_in_store_after_it_has_been_added(self):
        self.file_server.add_file_from_local_disk(self.test_epub_path, 'epub')
        self.assertTrue(self.file_server.is_file_in_store(self.test_epub_path, 'epub'))
        self.assertFalse(self.file_server.is_file_in_store(self.test_txt_path, 'txt'))


if __name__ == "__main__":
    unittest.main()

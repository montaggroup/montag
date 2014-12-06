import unittest
import sys
import os
import time
import tempfile

sys.path.append(os.getcwd())

import pydb.maindb

import logging

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("test_file_add_performance")

def print_results(testname, size, duration):
    throughput = size*1.0 / duration
    print("Results for {:>10}: {:8} kBps, {:7.1f} ms".format(testname, throughput/1000, round(duration * 1000, 1)))

def get_schema_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'db-schemas'))


class TestFileAddPerformance(unittest.TestCase):
    def setUp(self):
        pass

    def test_add_an_epub(self):

        for i in xrange(10):
            pydb_base_dir = tempfile.mkdtemp('pydb_file_add_performance')
            self.main_db = pydb.maindb.MainDB(pydb_base_dir, get_schema_dir())
            time.sleep(0.5)


            script_path = os.path.dirname(__file__)
            file_path = os.path.join(script_path, 'test_data', 'pg1661.epub')

            # read the file to fill the os cache
            test_file_contents = open(file_path, "rb").read()
            epub_size = len(test_file_contents)
            start_time = time.clock()
            self.main_db.add_file_from_local_disk(file_path, 'epub',
                                                  only_allowed_hash=None, move_file=False, strip_file=True)

            stop_time = time.clock()
            duration = stop_time - start_time

            print_results('epub', epub_size, duration)



        
if __name__ == "__main__":
    unittest.main()
    
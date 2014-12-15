import unittest
import pydb.maindb as main_db
import pydb.unittests
import mock

class TestMainDb(unittest.TestCase):
    def setUp(self):

        local_db = mock.MagicMock()
        friends_db = mock.MagicMock()
        merge_db = mock.MagicMock()
        store_dir = mock.MagicMock()
        build_foreign_db = mock.MagicMock()

        self.main_db = main_db.MainDB(local_db, friends_db, merge_db, store_dir, build_foreign_db)

    def testPing(self):
        self.assertEqual(self.main_db.ping(), 'pong')




if __name__ == '__main__':
    unittest.main()

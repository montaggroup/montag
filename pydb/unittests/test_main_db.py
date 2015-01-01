import unittest
import pydb.maindb as main_db
import pydb.unittests
import mock


class TestMainDb(unittest.TestCase):
    def setUp(self):

        local_db = mock.MagicMock()
        friends_db = mock.MagicMock()
        merge_db = mock.MagicMock()
        build_foreign_db = mock.MagicMock()
        index_server = mock.MagicMock()

        self.main_db = main_db.MainDB(local_db, friends_db, merge_db, build_foreign_db, index_server)

    def testPing(self):
        self.assertEqual(self.main_db.ping(), 'pong')

if __name__ == '__main__':
    unittest.main()

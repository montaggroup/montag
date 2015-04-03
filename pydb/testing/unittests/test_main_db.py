import unittest

import mock

import pydb.databases.maindb as main_db


class TestMainSetup(unittest.TestCase):
    def setUp(self):

        local_db = mock.MagicMock()
        friends_db = mock.MagicMock()
        merge_db = mock.MagicMock()
        build_foreign_db = mock.MagicMock()
        index_server = mock.MagicMock()

        self.main_db = main_db.MainDB(local_db, friends_db, merge_db, build_foreign_db, index_server)

    def testPing(self):
        self.assertEqual(self.main_db.ping(), 'pong')

class TestMainDbAutoCreateFidelity(unittest.TestCase):
    def test_auto_create_fidelity_of_positive_source_fidelity_is_smaller_than_source(self):
        self.assertLess(main_db._auto_create_fidelity(50), 50)


if __name__ == '__main__':
    unittest.main()



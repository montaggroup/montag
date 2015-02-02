import unittest

import logging
logger = logging.getLogger('test_author_add')

import os
import helpers


logging.basicConfig(level=logging.INFO)


def get_schema_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'db-schemas'))


class TestAddAuthor(unittest.TestCase):
    def setUp(self):
        self.main_db = helpers.build_main_db_memory_only(get_schema_dir())
        self.friend_1_id = self.main_db.add_friend('a friend')

    def test_adding_an_author_generates_a_name_key(self):
        self.main_db.add_author(name='john Smith_')
        authors = self.main_db.get_all_authors()
        self.assertEqual(len(authors), 1)
        first_author = authors[0]
        self.assertEqual(first_author['name'], 'john Smith_')
        self.assertEqual(first_author['name_key'], 'johnsmith')

    def test_after_adding_an_author_it_can_be_found_via_name_key(self):
        self.main_db.add_author(name='john Smith_')
        authors = self.main_db.find_authors_with_same_name_key('jo hnsmith')
        self.assertEqual(len(authors), 1)
        first_author = authors[0]
        self.assertEqual(first_author['name'], 'john Smith_')

    def test_after_adding_an_author_it_can_not_be_found_via_wrong_name_key(self):
        self.main_db.add_author(name='john Smith_')
        authors = self.main_db.find_authors_with_same_name_key('ji hnsmith')
        self.assertEqual(len(authors), 0)



if __name__ == '__main__':
    unittest.main()
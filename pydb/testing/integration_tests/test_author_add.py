# coding=utf-8
import unittest
import logging

from pydb.testing.integration_tests import helpers
import pydb.testing

logger = logging.getLogger('test_author_add')
logging.basicConfig(level=logging.INFO)


class TestAddAuthor(unittest.TestCase):
    def setUp(self):
        self.main_db = helpers.build_main_db_memory_only(pydb.testing.guess_schema_dir())

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

    def test_after_adding_we_can_retrieve_a_merge_document(self):
        id_ = self.main_db.add_author(name='john Smith')
        item = self.main_db.get_author(id_)
        guid = item['guid']
        author_doc = self.main_db.get_author_document_by_guid(guid)
        self.assertEqual(author_doc['name'], 'john Smith')

    def test_after_adding_we_can_retrieve_a_local_document(self):
        id_ = self.main_db.add_author(name='john Smith')
        item = self.main_db.get_author(id_)
        guid = item['guid']
        author_doc = self.main_db.get_local_author_document_by_guid(guid)
        self.assertEqual(author_doc['name'], 'john Smith')


class TestFindOrCreateAuthor(unittest.TestCase):
    def setUp(self):
        self.main_db = helpers.build_main_db_memory_only(pydb.testing.guess_schema_dir())

    def test_after_adding_a_author_find_or_create_add_author_won_t_add_another_one_having_the_same_name_key(self):
        id1 = self.main_db.find_or_create_author(author_name='john w. Smith', fidelity=60)
        id2 = self.main_db.find_or_create_author(author_name='john w smith', fidelity=60)
        self.assertEqual(id1, id2)

    def test_find_or_create_author_will_fall_back_to_exact_match_if_multiple_name_key_matches_exist(self):
        id1 = self.main_db.add_author(name='john w. Smith', date_of_birth="123")
        id2 = self.main_db.add_author(name='john w smith', date_of_birth="234")

        id3 = self.main_db.find_or_create_author(author_name='john w smith', fidelity=60)

        self.assertEqual(id2, id3)
        self.assertNotEqual(id1, id3)


if __name__ == '__main__':
    unittest.main()

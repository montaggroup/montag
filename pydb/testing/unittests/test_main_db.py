# coding=utf-8
import unittest
from collections import namedtuple
import mock

import pydb.maindb as main_db

MainDbMocks = namedtuple('MainDbMocks', 'local_db friends_db merge_db build_foreign_db indexserver')


def build_main_db_with_mocks():
    local_db = mock.MagicMock()
    friends_db = mock.MagicMock()
    merge_db = mock.MagicMock()
    build_foreign_db = mock.MagicMock()
    index_server = mock.MagicMock()

    mocks = MainDbMocks(local_db, friends_db, merge_db, build_foreign_db, index_server)
    db = main_db.MainDB(local_db, friends_db, merge_db, build_foreign_db, index_server)

    return db, mocks


class TestMainSetup(unittest.TestCase):
    def setUp(self):
        self.main_db, _ = build_main_db_with_mocks()

    def test_ping(self):
        self.assertEqual(self.main_db.ping(), 'pong')


class TestMainDbAutoCreateFidelity(unittest.TestCase):
    def test_auto_create_fidelity_of_positive_source_fidelity_is_smaller_than_source(self):
        self.assertLess(main_db._auto_create_fidelity(50), 50)


class TestMainDbFuseTomes(unittest.TestCase):
    def setUp(self):
        self.main_db, self.main_db_mocks = build_main_db_with_mocks()

    def test_fuse_tomes_happy_path_results_in_no_error(self):
        """ this test only tries to excercise the fuse tomes functions without any expectation of the result
        """
        self.main_db_mocks.merge_db.get_tome.return_value = {
            'id': 1,
            'guid': 1234,
            'fidelity': 40,
        }

        self.main_db_mocks.merge_db.get_tome_document_by_guid.return_value = {
            'id': 1,
            'fusion_sources': [],
            'guid': '1234',
            'authors': []
        }
        self.main_db.fuse_tomes('a', 'b')


class TestGetBestRelevantCoverAvailable(unittest.TestCase):
    def setUp(self):
        self.main_db, self.main_db_mocks = build_main_db_with_mocks()

    def test_if_no_covers_are_available_none_will_be_returned(self):
        self.main_db_mocks.merge_db.get_tome_files.return_value = []
        result = self.main_db.get_best_relevant_cover_available(tome_id=1)
        self.assertIsNone(result)

    def test_if_one_cover_is_avaiable_with_fidelity_to_low_none_will_be_returned(self):
        self.main_db_mocks.merge_db.get_tome_files.return_value = [{'fidelity': 15,
                                                                    'hash': 'aaaaa1234'}]

        result = self.main_db.get_best_relevant_cover_available(tome_id=1)
        self.assertIsNone(result)


class TestGetTomeByGuid(unittest.TestCase):
    def setUp(self):
        self.main_db, self.main_db_mocks = build_main_db_with_mocks()
        self.main_db_mocks.merge_db.get_tome_document_by_guid.return_value = {
            'title': 'a tome',
            'guid': ' 1234',
            'tags': [
                {
                    'tag_value': '%this_is_private',
                    'fidelity': 70
                },
                {
                    'tag_value': 'this_is_not_private',
                    'fidelity': 80
                },
                {
                    'tag_value': '<this_is_detail',
                    'fidelity': 80
                }
            ]
        }

    def test_if_hide_private_tags_is_disabled_all_tags_are_returned(self):
        doc = self.main_db.get_tome_document_by_guid('1234', hide_private_tags=False)

        tags = doc['tags']
        self.assertEqual(len(tags), 3)

    def test_if_hide_private_tags_is_enabled_private_tags_are_not_returned(self):
        doc = self.main_db.get_tome_document_by_guid('1234', hide_private_tags=True)

        tags = doc['tags']
        self.assertEqual(len(tags), 2)


if __name__ == '__main__':
    unittest.main()

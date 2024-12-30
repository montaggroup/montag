import unittest
import copy
import logging

from pydb.testing.integration_tests import helpers
import pydb.testing


logger = logging.getLogger('test_tome_fusion')
logging.basicConfig(level=logging.INFO)


author_doc_1 = {
    'name': 'some body',
    'fusion_sources': [],
    'fidelity': 60.0,
    'guid': 'aaaaaaaaaabbbbbbbbbbccccccccccd1',
    'date_of_birth': '2014-01-01',
    'date_of_death': '2014-01-02'
}

author_doc_2 = {
    'name': 'another body',
    'fusion_sources': [],
    'fidelity': 80.0,
    'guid': 'aaaaaaaaaabbbbbbbbbbccccccccccd2',
    'date_of_birth': '2015-01-01',
    'date_of_death': '2015-01-02'
}

tome_author_1_doc = {
    'title': 'a tome',
    'subtitle': 'a tome',
    'fusion_sources': [],
    'fidelity': 60.0,
    'guid': 'baaaaaaaaaabbbbbbbbbbcccccccccc1',
    'principal_language': 'en',
    'publication_year': None,
    'files': [{
        'hash': 'aa',
        'fidelity': '50',
        'file_extension': 'epub',
        'file_type': 1,
        'size': 10
    }],
    'tags': [],
    'edition': None,
    'authors': [{
        'guid': 'aaaaaaaaaabbbbbbbbbbccccccccccd1',
        'order': 1,
        'fidelity': 60
    }],
    'synopses': [],
    'type': 1
}

tome_author_2_doc = copy.deepcopy(tome_author_1_doc)
tome_author_2_doc['title'] = 'b tome'
tome_author_2_doc['guid'] = 'baaaaaaaaaabbbbbbbbbbcccccccccc2'
tome_author_2_doc['authors'] = [{'guid': 'aaaaaaaaaabbbbbbbbbbccccccccccd2',
                                 'order': 1,
                                 'fidelity': 65}]


class TestTomeFusion(unittest.TestCase):
    def setUp(self):
        self.main_db = helpers.build_main_db_memory_only(pydb.testing.guess_schema_dir())
        self.main_db.load_own_author_document(author_doc_1)
        self.main_db.load_own_author_document(author_doc_2)
        self.main_db.load_own_tome_document(tome_author_1_doc)
        self.main_db.load_own_tome_document(tome_author_2_doc)

        self.assertEqual(len(self.main_db.get_all_authors()), 2)
        self.assertEqual(len(self.main_db.get_all_tomes()), 2)

    def test_fusing_both_tomes_leads_to_one_tome_having_both_authors_direction_1(self):
        self.main_db.fuse_tomes(tome_author_1_doc['guid'], tome_author_2_doc['guid'])

        result_tome = self.main_db.get_tome_document_by_guid(tome_author_2_doc['guid'])
        self.assertEqual(result_tome['title'], 'b tome')
        self.assertEqual(len(result_tome['authors']), 2)

    def test_fusing_both_tomes_leads_to_one_tome_having_both_authors_direction_2(self):
        self.main_db.fuse_tomes(tome_author_2_doc['guid'], tome_author_1_doc['guid'])

        result_tome = self.main_db.get_tome_document_by_guid(tome_author_2_doc['guid'])
        self.assertEqual(result_tome['title'], 'a tome')
        self.assertEqual(len(result_tome['authors']), 2)



if __name__ == '__main__':
    unittest.main()

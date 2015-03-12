import unittest
import copy
import os
import helpers


import logging
logger = logging.getLogger('test_author_fusion')
logging.basicConfig(level=logging.INFO)


def get_schema_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'db-schemas'))


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

tome_author_both_doc = copy.deepcopy(tome_author_1_doc)
tome_author_both_doc['authors'].append({
        'guid': 'aaaaaaaaaabbbbbbbbbbccccccccccd2',
        'order': 1,
        'fidelity': 65
})

class TestAuthorFusion(unittest.TestCase):
    def setUp(self):
        self.main_db = helpers.build_main_db_memory_only(get_schema_dir())
        self.main_db.load_own_author_document(author_doc_1)
        self.main_db.load_own_author_document(author_doc_2)

        self.assertEqual(len(self.main_db.get_all_authors()), 2)

    def test_fusing_two_authors_results_in_having_one_less_author(self):
        author_doc_2b = copy.deepcopy(author_doc_2)
        author_doc_2b['fusion_sources'] = [{'fidelity': 60,
                                            'source_guid': author_doc_1['guid']}]

        self.main_db.load_own_author_document(author_doc_2b)

        self.assertEqual(len(self.main_db.get_all_authors()), 1)

    def test_fusing_two_authors_results_the_remaining_author_keeping_its_name(self):
        author_doc_2b = copy.deepcopy(author_doc_2)
        author_doc_2b['fusion_sources'] = [{'fidelity': 60,
                                            'source_guid': author_doc_1['guid']}]

        self.main_db.load_own_author_document(author_doc_2b)

        all_authors = self.main_db.get_all_authors()
        author = all_authors[0]
        self.assertEqual(author['name'], 'another body')

    def test_fusing_two_authors_results_the_remaining_author_keeping_its_name_even_if_fidelity_smaller_than_source(self):
        author_doc_2b = copy.deepcopy(author_doc_2)
        author_doc_2b['fidelity'] = 45
        author_doc_2b['fusion_sources'] = [{'fidelity': 60,
                                            'source_guid': author_doc_1['guid']}]

        self.main_db.load_own_author_document(author_doc_2b)

        all_authors = self.main_db.get_all_authors()
        author = all_authors[0]
        self.assertEqual(author['name'], 'another body')
        print author


class TestAuthorFusionTomeChanges(unittest.TestCase):
    def setUp(self):
        self.main_db = helpers.build_main_db_memory_only(get_schema_dir())
        self.main_db.load_own_author_document(author_doc_1)
        self.main_db.load_own_author_document(author_doc_2)

        self.assertEqual(len(self.main_db.get_all_authors()), 2)

    def _fuse_authors(self):
        author_doc_2b = copy.deepcopy(author_doc_2)
        author_doc_2b['fusion_sources'] = [{'fidelity': 60,
                                            'source_guid': author_doc_1['guid']}]
        self.main_db.load_own_author_document(author_doc_2b)

    def test_after_fusing_two_authors_affected_locally_created_tome_is_linking_against_the_fusion_target(self):
        self.main_db.load_own_tome_document(tome_author_1_doc)

        self._fuse_authors()

        # check merge db output
        result_tome = self.main_db.get_tome_document_by_guid(tome_author_1_doc['guid'])

        self.assertEqual(len(result_tome['authors']), 1)
        author = result_tome['authors'][0]
        self.assertEqual(author['guid'], 'aaaaaaaaaabbbbbbbbbbccccccccccd2')

    def test_after_fusing_two_authors_affected_remotely_created_tome_is_linking_against_the_fusion_target(self):
        self.main_db.add_friend('friend')
        self.main_db.load_author_documents_from_friend(1, [author_doc_1])
        self.main_db.load_tome_documents_from_friend(1, [tome_author_1_doc])

        self._fuse_authors()

        result_tome = self.main_db.get_tome_document_by_guid(tome_author_1_doc['guid'])

        self.assertEqual(len(result_tome['authors']), 1)
        author = result_tome['authors'][0]
        self.assertEqual(author['guid'], 'aaaaaaaaaabbbbbbbbbbccccccccccd2')

    def test_after_fusing_two_authors_a_locally_created_tome_by_both_authors_only_has_one_author(self):
        self.assertEqual(len(tome_author_both_doc['authors']), 2)
        self.main_db.load_own_tome_document(tome_author_both_doc)

        self._fuse_authors()

        # check merge db output
        result_tome = self.main_db.get_tome_document_by_guid(tome_author_both_doc['guid'])

        self.assertEqual(len(result_tome['authors']), 1)
        author = result_tome['authors'][0]
        self.assertEqual(author['guid'], 'aaaaaaaaaabbbbbbbbbbccccccccccd2')


if __name__ == '__main__':
    unittest.main()

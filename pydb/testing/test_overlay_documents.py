import unittest
import copy

import logging
logger = logging.getLogger('test_overlay_documents')

import os
import helpers


logging.basicConfig(level=logging.INFO)


def get_schema_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'db-schemas'))


tome_doc_friend_1 = {
    'title': 'a tome',
    'subtitle': 'a tome',
    'fusion_sources': [],
    'fidelity': 60.0,
    'guid': 'aaaaaaaaaabbbbbbbbbbccccccccccd1',
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
    'authors': [],
    'synopses': [],
    'type': 1
}

tome_doc_local_template = {
    'title': 'a tome',
    'subtitle': 'a tome',
    'fusion_sources': [],
    'fidelity': 80.0,
    'guid': 'aaaaaaaaaabbbbbbbbbbccccccccccd1',
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
    'authors': [],
    'edition': None,
    'synopses': [],
    'type': 1
}


def _build_local_doc(file_fidelity=50):
    result = copy.deepcopy(tome_doc_local_template)
    result['files'][0]['fidelity'] = file_fidelity
    return result


class TestOverlayDocuments(unittest.TestCase):
    def setUp(self):
        self.main_db = helpers.build_main_db_memory_only(get_schema_dir())
        self.friend_1_id = self.main_db.add_friend('a friend')

        self.main_db.load_tome_documents_from_friend(self.friend_1_id, [tome_doc_friend_1])

    def test_with_only_a_merge_db_entry_it_is_returned(self):
        result = self.main_db.get_tome_document_with_local_overlay_by_guid('aaaaaaaaaabbbbbbbbbbccccccccccd1')

        self.assertEqual(len(result['files']), 1)
        self.assertEqual(result['files'][0]['fidelity'], 45.0)

    def test_with_a_large_negative_local_fidelity_value_a_entry_with_negative_fidelity_is_returned(self):
        loc = _build_local_doc(-80)
        self.main_db.load_own_tome_document(loc)

        result = self.main_db.get_tome_document_with_local_overlay_by_guid('aaaaaaaaaabbbbbbbbbbccccccccccd1')

        self.assertEqual(len(result['files']), 1)
        self.assertEqual(result['files'][0]['fidelity'], -80.0)

    def test_with_a_small_negative_local_fidelity_value_no_entry_is_returned(self):
        loc = _build_local_doc(-40)
        self.main_db.load_own_tome_document(loc)

        result = self.main_db.get_tome_document_with_local_overlay_by_guid('aaaaaaaaaabbbbbbbbbbccccccccccd1')

        self.assertEqual(len(result['files']), 1)
        self.assertEqual(result['files'][0]['fidelity'], -40.0)


if __name__ == '__main__':
    unittest.main()

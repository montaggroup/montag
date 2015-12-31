import unittest
import pydb.indexthread


class TestFetchTomes(unittest.TestCase):
    def setUp(self):
        self.merge_db = MockMergeDB()

    def test_an_author_with_low_link_fidelity_is_not_added(self):
        self.merge_db.tome_guid_to_id['guid1'] = 1

        self.merge_db.tomes[1] = {
            'id': 1,
            'title': 'a tome'
        }
        self.merge_db.tome_authors[1] = [{
            'name': 'low link',
            'link_fidelity': 10,
            'fidelity': 90
        }, {
            'name': 'high link',
            'link_fidelity': 90,
            'fidelity': 90
        }]

        deleted_tome_guids, tomes_with_authors_and_tags = pydb.indexthread._fetch_tomes(self.merge_db, ['guid1'])

        self.assertFalse(deleted_tome_guids)
        self.assertEqual(len(tomes_with_authors_and_tags), 1)
        tome = tomes_with_authors_and_tags[0]
        self.assertEqual(tome['title'], 'a tome')
        authors = tome['authors']
        self.assertEqual(len(authors), 1)
        author = authors[0]
        self.assertEqual(author['name'], 'high link')


class MockMergeDB(object):
    def __init__(self):
        self.tomes = {}
        self.tome_guid_to_id = {}
        self.tome_authors = {}
        self.tome_tags = {}

    def get_tome_by_guid(self, tome_guid):
        if tome_guid not in self.tome_guid_to_id:
            return None
        tome_id = self.tome_guid_to_id[tome_guid]
        return self.tomes[tome_id]

    def get_tome_authors(self, tome_id):
        tome_id = int(tome_id)
        if tome_id in self.tome_authors:
            return self.tome_authors[tome_id]
        return []

    def get_tome_tags(self, tome_id):
        tome_id = int(tome_id)
        if tome_id in self.tome_tags:
            return self.tome_tags[tome_id]
        return []



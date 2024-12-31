import unittest
import pydb.documents as documents
import json
import mock
import copy


class TestPrepareTomeDocument(unittest.TestCase):
    def setUp(self):
        self.tome_doc_string = """
{
  "files": [
    {
      "file_type": 1,
      "file_extension": "pdf",
      "hash": "a_hash",
      "fidelity": 80.0,
      "size": 1000
    }
  ],
  "principal_language": "en",
  "subtitle": null,
  "tags": [],
  "fusion_sources": [],
  "title": "Oliver Twist",
  "publication_year": null,
  "edition": null,
  "synopses": [
  {
      "content": "",
      "fidelity": 80.0,
      "guid": "s1_guid"
  },
  {
      "content": "do not delete me, i am not empty! i have an elderly parent!",
      "fidelity": 80.0,
      "guid": "s2_guid"
  }
  ],
  "authors": [
    {
      "fidelity": 60.0,
      "guid": "dickens_guid",
      "order": 0.0
    }
  ],
  "fidelity": 50.0,
  "guid": "guid",
  "type": 1
}
"""
        self.tome_doc = json.loads(self.tome_doc_string)

    def test_removes_empty_synopses(self):
        self.assertEqual(len(self.tome_doc['synopses']), 2)
        self.local_db = mock.MagicMock()
        new_doc = documents.prepare_tome_document(self.tome_doc, self.local_db)
        self.assertEqual(len(new_doc['synopses']), 1)


class TestPrepareAuthorDocument(unittest.TestCase):
    def setUp(self):
        self.author_doc_string = """
{
  "name": "some body",
  "fusion_sources": [],
  "fidelity": 50.0,
  "guid": "guid",
  "date_of_birth": "2014-01-01",
  "date_of_death": "2014-01-02"
}
"""
        self.author = json.loads(self.author_doc_string)

    def test_raises_no_error_on_valid_document(self):
        prepped = documents.prepare_author_document(self.author)
        self.assertEqual(prepped['fidelity'], 50.0)
        self.assertEqual(prepped['guid'], 'guid')
        self.assertEqual(prepped['name'], 'some body')
        self.assertEqual(prepped['date_of_birth'], '2014-01-01')
        self.assertEqual(prepped['date_of_death'], '2014-01-02')
        self.assertFalse(prepped['fusion_sources'])

    def test_raises_value_error_on_non_float_fidelity(self):
        a = copy.deepcopy(self.author)
        a['fidelity'] = '9a'

        with self.assertRaises(ValueError):
            documents.prepare_author_document(a)


if __name__ == '__main__':
    unittest.main()

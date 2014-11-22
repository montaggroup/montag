import unittest
import pydb.documents as documents
import json
import mock

class test_overlay_document(unittest.TestCase):
    def test_overlay_with_merge_entry_none_returns_none(self):
        self.assertIsNone(documents.overlay_document(None, {}))

    def test_overlay_with_local_entry_none_returns_merge_entry(self):
        overlay = documents.overlay_document({'a': 'b'}, None)
        self.assertIn('a', overlay)
        self.assertEqual('b', overlay['a'])

    def test_overlay_merge_db_high_fidelity_file_is_kept(self):
        merge_document = {'files': [{'hash': '1234', 'fidelity': 80}]}
        local_document = {'files': [{'hash': '1234', 'fidelity': 60}]}

        overlay = documents.overlay_document(merge_document, local_document)
        result_files = overlay['files']
        self.assertEqual(len(result_files), 1)
        result_file = result_files[0]
        self.assertEqual(result_file['fidelity'], 80)

    def test_overlay_merge_db_high_fidelity_tag_is_kept(self):
        merge_document = {'tags': [{'tag_value': '1234', 'fidelity': 70}]}
        local_document = {'tags': [{'tag_value': '1234', 'fidelity': 10}]}

        overlay = documents.overlay_document(merge_document, local_document)
        result_tags = overlay['tags']
        self.assertEqual(len(result_tags), 1)
        result_tag = result_tags[0]
        self.assertEqual(result_tag['fidelity'], 70)
        self.assertEqual(result_tag['fidelity'], 70)

    def test_overlay_merge_db_high_fidelity_file_is_unconcerned_by_unrelated_file(self):
        merge_document = {'files': [{'hash': '1234', 'fidelity': 80}]}
        local_document = {'files': [{'hash': '12345', 'fidelity': -10}]}

        overlay = documents.overlay_document(merge_document, local_document)
        result_files = overlay['files']
        self.assertEqual(len(result_files), 1)
        result_file = result_files[0]
        self.assertEqual(result_file['fidelity'], 80)

    def test_overlay_merge_db_high_fidelity_file_is_overwritten_by_negative_local_fidelity(self):
        merge_document = {'files': [{'hash': '1234', 'fidelity': 80}]}
        local_document = {'files': [{'hash': '1234', 'fidelity': -10}]}

        overlay = documents.overlay_document(merge_document, local_document)
        result_files = overlay['files']
        self.assertEqual(len(result_files), 1)
        result_file = result_files[0]
        self.assertEqual(result_file['fidelity'], -10)

    def test_overlay_merge_db_tag_is_overwritten_by_negative_local_fidelity(self):
        merge_document = {'tags': [{'tag_value': '1234', 'fidelity': 10}]}
        local_document = {'tags': [{'tag_value': '1234', 'fidelity': -10}]}

        overlay = documents.overlay_document(merge_document, local_document)
        result_tags = overlay['tags']
        self.assertEqual(len(result_tags), 1)
        result_tag = result_tags[0]
        self.assertEqual(result_tag['fidelity'], -10)


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

if __name__ == '__main__':
    unittest.main()

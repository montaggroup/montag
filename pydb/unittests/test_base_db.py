import unittest

import pydb.basedb as basedb
import pydb.mergedb as mergedb
import pydb.unittests
from pydb import TomeType
import copy


class test_tome_statistics(unittest.TestCase):
    def setUp(self):
        # a merge db derives from base db
        self.merge_db = mergedb.MergeDB(":memory:", pydb.unittests.guess_schema_path(), enable_db_sync=False)
        self.assertTrue(isinstance(self.merge_db, basedb.BaseDB))

    def test_empty(self):
        m = self.merge_db

        stats = m.get_tome_statistics()
        self.assertFalse(stats)

    def test_one_english_nonfiction_tome(self):
        m = self.merge_db

        m.insert_object("tomes", {'title': 'a', 'fidelity': '50', 'guid': 'b',
                                  'principal_language': 'en', 'type': TomeType.NonFiction})

        stats = m.get_tome_statistics()
        self.assertEqual(len(stats), 1)

        self.assertIn('en', stats)
        en_stat = stats['en']

        self.assertEqual(en_stat[TomeType.NonFiction], 1)
        self.assertEqual(en_stat[TomeType.Fiction], 0)

    def test_two_english_fiction_tomes(self):
        m = self.merge_db

        m.insert_object("tomes", {'title': 'a', 'fidelity': '50', 'guid': 'b',
                                  'principal_language': 'en', 'type': TomeType.Fiction})
        m.insert_object("tomes", {'title': 'a1', 'fidelity': '50', 'guid': 'b1',
                                  'principal_language': 'en', 'type': TomeType.Fiction})

        stats = m.get_tome_statistics()
        self.assertEqual(len(stats), 1)

        self.assertIn('en', stats)
        en_stat = stats['en']

        self.assertEqual(en_stat[TomeType.NonFiction], 0)
        self.assertEqual(en_stat[TomeType.Fiction], 2)

    def test_two_different_language_tomes(self):
        m = self.merge_db

        m.insert_object("tomes", {'title': 'a', 'fidelity': '50',
                                  'guid': 'b', 'principal_language': 'en', 'type': TomeType.Fiction})
        m.insert_object("tomes", {'title': 'a1', 'fidelity': '50',
                                  'guid': 'b1', 'principal_language': 'es', 'type': TomeType.Fiction})

        stats = m.get_tome_statistics()
        self.assertEqual(len(stats), 2)

        # check the en one        
        self.assertIn('en', stats)
        en_stat = stats['en']

        self.assertEqual(en_stat[TomeType.NonFiction], 0)
        self.assertEqual(en_stat[TomeType.Fiction], 1)

        # check the es one
        self.assertIn('es', stats)
        es_stat = stats['es']

        self.assertEqual(es_stat[TomeType.NonFiction], 0)
        self.assertEqual(es_stat[TomeType.Fiction], 1)


# noinspection PyProtectedMember
class test_schema_version(unittest.TestCase):
    def setUp(self):
        # a merge db derives from base db
        self.merge_db = mergedb.MergeDB(":memory:", pydb.unittests.guess_schema_path(), enable_db_sync=False)
        self.assertTrue(isinstance(self.merge_db, basedb.BaseDB))

    def test_after_set_schema_version_to_two_read_schema_version_should_return_two(self):
        self.merge_db._set_schema_version(2)
        self.assertEquals(2, self.merge_db._get_schema_version())

    def test_after_set_schema_version_to_zero_read_schema_version_should_return_zero(self):
        self.merge_db._set_schema_version(0)
        self.assertEquals(0, self.merge_db._get_schema_version())


class test_data_files_equal(unittest.TestCase):
    def test_file_compare_two_exact_copies_should_return_true(self):
        file_a = {
            "file_type": 1,
            "file_extension": "epub",
            "hash": "aa",
            "fidelity": 60.0,
            "size": 1951
        }

        file_b = copy.deepcopy(file_a)
        self.assertTrue(basedb.data_fields_equal(file_a, file_b))

    def test_file_compare_should_ignore_local_file_exists(self):
        file_a = {
            "file_type": 1,
            "file_extension": "epub",
            "hash": "aa",
            "fidelity": 60.0,
            "size": 1951
        }

        file_b = copy.deepcopy(file_a)
        file_b['local_file_exists'] = 1

        self.assertTrue(basedb.data_fields_equal(file_a, file_b))


if __name__ == '__main__':
    unittest.main()

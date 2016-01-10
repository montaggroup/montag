# coding=utf-8
import unittest
import logging

from pydb import mergedb
from pydb import FileType
import pydb.testing.unittests

logging.basicConfig()


class TestCalculateItemsDifference(unittest.TestCase):
    def setUp(self):
        pass

    def test_remove_one(self):
        old_items = {'a': 'a_content'}
        new_items = {}

        keys_to_add, keys_to_remove, keys_to_check = mergedb.calculate_items_difference(old_items, new_items)
        self.assertFalse(keys_to_add)
        self.assertTrue(keys_to_remove)
        self.assertFalse(keys_to_check)

        self.assertIn('a', keys_to_remove)
        self.assertEquals(len(keys_to_remove), 1)

    def test_add_one(self):
        old_items = {'b': 'b_content'}
        new_items = {'a': 'a_content', 'b': 'b_content'}

        keys_to_add, keys_to_remove, keys_to_check = mergedb.calculate_items_difference(old_items, new_items)
        self.assertTrue(keys_to_add)
        self.assertFalse(keys_to_remove)

        self.assertIn('a', keys_to_add)
        self.assertEquals(len(keys_to_add), 1)

    def test_check_one(self):
        old_items = {'b': 'b_content'}
        new_items = {'a': 'a_content', 'b': 'b_content'}

        keys_to_add, keys_to_remove, keys_to_check = mergedb.calculate_items_difference(old_items, new_items)

        self.assertIn('b', keys_to_check)
        self.assertEquals(len(keys_to_check), 1)


class TestDeleteAll(unittest.TestCase):
    def setUp(self):
        self.merge_db = mergedb.MergeDB(":memory:", pydb.testing.guess_schema_dir(),
                                        local_db=None, enable_db_sync=False)

    def test_delete_all_tomes_table(self):
        m = self.merge_db

        tome_id = m.insert_object("tomes", {'title': 'a', 'guid': 'b', 'principal_language': 'c'})
        tome = m.get_tome(tome_id)
        self.assertIsNotNone(tome)
        m.delete_all()
        tome = m.get_tome(tome_id)
        self.assertIsNone(tome)

    def test_delete_all_local_files_table(self):
        m = self.merge_db

        m.insert_object("local_files", {'hash': 'a', 'file_extension': 'b'})
        file_item = m.get_local_file('a')
        self.assertIsNotNone(file_item)
        m.delete_all()
        file_item = m.get_local_file('a')
        self.assertIsNone(file_item)


def _insert_tome_with_file(merge_db, tome_fidelity, file_fidelity, tome_id=1, tome_guid='a', file_hash='hashf1'):
    merge_db.insert_object("tomes", {'id': tome_id,
                                     'guid': tome_guid,
                                     'title': 'a',
                                     'principal_language': 'en',
                                     'fidelity': tome_fidelity})

    merge_db.insert_object("files", {'tome_id': 1,
                                     'file_type': FileType.Content,
                                     'hash': file_hash,
                                     'file_extension': 'b',
                                     'size': 10,
                                     'fidelity': file_fidelity})


class TestGetHighFidelityTomeFileHashesWithoutLocalFile(unittest.TestCase):
    def setUp(self):
        self.merge_db = mergedb.MergeDB(":memory:", pydb.testing.guess_schema_dir(),
                                        local_db=None, enable_db_sync=False)

    def test_empty(self):
        hashes = self.merge_db.get_high_fidelity_tome_file_hashes_without_local_file(
            min_tome_fidelity=0, min_file_fidelity=0, max_file_size_to_request_bytes=100000, max_items=10)
        hashes = list(hashes)
        self.assertEquals(len(hashes), 0)

    def test_single_tome_allowed(self):
        _insert_tome_with_file(self.merge_db, tome_fidelity=30, file_fidelity=30)

        hashes = self.merge_db.get_high_fidelity_tome_file_hashes_without_local_file(
            min_tome_fidelity=0, min_file_fidelity=0, max_file_size_to_request_bytes=100000, max_items=10)
        hashes = list(hashes)

        self.assertEquals(len(hashes), 1)
        a = hashes[0]
        self.assertEquals(a, 'hashf1')

    def test_single_tome_with_file_fidelity_to_low(self):
        _insert_tome_with_file(self.merge_db, tome_fidelity=30, file_fidelity=30)

        hashes = self.merge_db.get_high_fidelity_tome_file_hashes_without_local_file(
            min_tome_fidelity=0, min_file_fidelity=31, max_file_size_to_request_bytes=100000, max_items=10)
        hashes = list(hashes)

        self.assertEquals(len(hashes), 0)

    def test_single_tome_with_tome_fidelity_to_low(self):
        _insert_tome_with_file(self.merge_db, tome_fidelity=30, file_fidelity=30)

        hashes = self.merge_db.get_high_fidelity_tome_file_hashes_without_local_file(
            min_tome_fidelity=31, min_file_fidelity=0, max_file_size_to_request_bytes=100000, max_items=10)
        hashes = list(hashes)

        self.assertEquals(len(hashes), 0)

    def test_two_tomes_allowed(self):
        _insert_tome_with_file(self.merge_db, tome_fidelity=30, file_fidelity=30, tome_id=1, tome_guid="ag",
                               file_hash="h1")
        _insert_tome_with_file(self.merge_db, tome_fidelity=30, file_fidelity=30, tome_id=2, tome_guid="bg",
                               file_hash="h2")

        hashes = self.merge_db.get_high_fidelity_tome_file_hashes_without_local_file(
            min_tome_fidelity=0, min_file_fidelity=0, max_file_size_to_request_bytes=100000, max_items=10)
        hashes = list(hashes)

        self.assertEquals(len(hashes), 2)

    def test_max_items_reduces_output_size(self):
        _insert_tome_with_file(self.merge_db, tome_fidelity=30, file_fidelity=30, tome_id=1, tome_guid="ag",
                               file_hash="h1")
        _insert_tome_with_file(self.merge_db, tome_fidelity=30, file_fidelity=30, tome_id=2, tome_guid="bg",
                               file_hash="h2")

        hashes = self.merge_db.get_high_fidelity_tome_file_hashes_without_local_file(
            min_tome_fidelity=0, min_file_fidelity=0, max_file_size_to_request_bytes=100000, max_items=1)
        hashes = list(hashes)

        self.assertEquals(len(hashes), 1)

    def test_local_available_file_not_returned(self):
        _insert_tome_with_file(self.merge_db, tome_fidelity=30, file_fidelity=30, file_hash="h1")
        m = self.merge_db
        m.insert_local_file({'hash': 'h1', 'file_extension': 'ext'})

        hashes = self.merge_db.get_high_fidelity_tome_file_hashes_without_local_file(
            min_tome_fidelity=0, min_file_fidelity=0, max_file_size_to_request_bytes=100000, max_items=10)
        hashes = list(hashes)

        self.assertEquals(len(hashes), 0)


class TestGetTomeDocument(unittest.TestCase):
    def setUp(self):
        self.merge_db = mergedb.MergeDB(":memory:", pydb.testing.guess_schema_dir(),
                                        local_db=None, enable_db_sync=False)

    def test_get_tome_document_by_guid_should_not_include_localFileExists(self):
        _insert_tome_with_file(self.merge_db, tome_fidelity=50, file_fidelity=50, tome_guid='guiiid')

        doc = self.merge_db.get_tome_document_by_guid('guiiid')
        self.assertIsNotNone(doc)
        file_link = doc['files'][0]
        self.assertNotIn('local_file_exists', file_link)


class TestItemWithBestOpinionUnipolar(unittest.TestCase):
    def test_having_two_items_with_different_fidelity_the_max_fidelity_item_is_returned(self):

        item_a = {'fidelity': 30, 'text': 'a'}
        item_b = {'fidelity': 40, 'text': 'b'}

        result = mergedb.item_with_best_opinion_unipolar([item_a, item_b])

        self.assertEqual(result['fidelity'], 40)
        self.assertEqual(result['text'], 'b')


class TestItemWithBestOpinionBipolar(unittest.TestCase):
    def setUp(self):
        self.item_a = {'fidelity': 30, 'text': 'a', 'last_modification_date': 1}
        self.item_b = {'fidelity': 40, 'text': 'a'}
        self.item_c = {'fidelity': -10, 'text': 'a'}
        self.item_d = {'fidelity': -50, 'text': 'a', 'last_modification_date': 4}

        self.result = None

    def given(self, item_group):
        self.result = mergedb.item_with_best_opinion_bipolar(item_group)

    def expect(self, fidelity):
        self.assertEqual(self.result['fidelity'], fidelity)

    def test_having_only_one_item_returns_that(self):
        self.given(mergedb.BipolarGroup(local_opinions=[], all_opinions=[self.item_a]))
        self.expect(30)

    def test_having_two_items_with_positive_fidelity_it_will_return_the_max(self):
        self.given(mergedb.BipolarGroup(local_opinions=[], all_opinions=[self.item_a, self.item_b]))
        self.expect(40)

    def test_having_two_items_with_positive_and_negative_fidelity_it_will_return_the_difference_as_effective_fidelity(self):
        self.given(mergedb.BipolarGroup(local_opinions=[], all_opinions=[self.item_a, self.item_c]))
        self.expect(20)

    def test_local_fidelity_overrides_merge_if_local_negative_and_merge_positive(self):
        self.given(mergedb.BipolarGroup(local_opinions=[self.item_a], all_opinions=[self.item_a, self.item_c]))
        self.expect(30)

    def test_using_two_local_items_the_newer_one_will_win(self):
        local_ops = [self.item_a,  self.item_d]
        self.given(mergedb.BipolarGroup(local_opinions=local_ops, all_opinions=local_ops))
        self.expect(-50)

    def test_using_two_local_items_the_newer_one_will_win_different_order(self):
        local_ops = [self.item_d,  self.item_a]
        self.given(mergedb.BipolarGroup(local_opinions=local_ops, all_opinions=local_ops))
        self.expect(-50)


class TestMergeItemsBipolar(unittest.TestCase):
    def setUp(self):
        self.item_a = {'fidelity': 30, 'text': 'a', 'last_modification_date': 1}
        self.item_a_neg = {'fidelity': -5, 'text': 'a', 'last_modification_date': 2}
        self.item_b = {'fidelity': 40, 'text': 'b', 'last_modification_date': 3}

    def test_having_only_one_item_returns_that(self):
        result = mergedb.merge_items_bipolar([], [self.item_a], lambda x: x['text'])
        self.assertEqual(len(result), 1)
        self.assertEqual(result['a']['fidelity'], 30)

    def test_having_two_different_items_returns_those(self):
        result = mergedb.merge_items_bipolar([], [self.item_a, self.item_b], lambda x: x['text'])
        self.assertEqual(len(result), 2)
        self.assertEqual(result['a']['fidelity'], 30)
        self.assertEqual(result['b']['fidelity'], 40)

    def test_having_two_diffent_opinions_negative_and_positive_and_effective_value_will_be_calculated(self):
        result = mergedb.merge_items_bipolar([], [self.item_a, self.item_a_neg], lambda x: x['text'])
        self.assertEqual(len(result), 1)
        self.assertEqual(result['a']['fidelity'], 25)


class TestExtractAuthoritativeLocalOpinion(unittest.TestCase):
    def setUp(self):
        self.item_a = {'fidelity': 30, 'text': 'a'}
        self.item_b = {'fidelity': 40, 'text': 'a'}
        self.item_c = {'fidelity': -30, 'text': 'a', 'last_modification_date': 10}
        self.item_d = {'fidelity': -40, 'text': 'a', 'last_modification_date': 2}

    def given(self, local_opinions):
        self.result = mergedb.extract_authoritative_local_opinion(local_opinions)

    def expect(self, expected_result):
        self.assertEqual(self.result, expected_result)

    def test_empty_opinion_list_returns_none(self):
        self.given([])
        self.expect(None)

    def test_list_with_single_item_returns_that_item(self):
        self.given([self.item_a])
        self.expect(self.item_a)

    def test_list_with_two_negative_entries_returns_the_newer_one(self):
        self.given([self.item_c, self.item_d])
        self.expect(self.item_c)


if __name__ == '__main__':
    unittest.main()

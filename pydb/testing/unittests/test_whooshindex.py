import unittest

from pydb import whooshindex


class TestWhooshIndexQuerySimplifier(unittest.TestCase):
    def assert_simplified(self, query, expected_result):
        result = whooshindex.simplify_query(query)
        self.assertEqual(result, expected_result)

    def asterisk_only_is_kept(self):
        self.assert_simplified('*', '*')

    def test_asterisk_in_complex_query_is_removed(self):
        self.assert_simplified('* principal_language:en', 'principal_language:en')



# coding=utf-8

import unittest
from pydb.names import calc_author_name_key


class TestCalcAuthorNameKey(unittest.TestCase):
    def test_different_author_names_result_in_different_keys(self):
        self.assertNotEqual(calc_author_name_key('John Smith'), calc_author_name_key('Joe Smith'))

    def test_author_swapped_at_comma_results_in_key_identical(self):
        self.assertEqual(calc_author_name_key('John Smith'), calc_author_name_key('Smith, John'))

    def test_spaces_in_author_name_do_not_matter(self):
        self.assertEqual(calc_author_name_key('John Smith'), calc_author_name_key('    John   Smith '))

    def test_punctuation_in_author_name_do_not_matter(self):
        self.assertEqual(calc_author_name_key('J Smith'), calc_author_name_key('J. Smith'))

    def test_case_of_author_name_do_not_matter(self):
        self.assertEqual(calc_author_name_key('j Smith'), calc_author_name_key('J smith'))

    def test_similar_umlauts_of_author_name_do_not_matter(self):
        self.assertEqual(calc_author_name_key(u'jøn smith'), calc_author_name_key(u'jǿn smith'))

    def test_similar_umlauts_of_author_name_do_not_matter_2(self):
        self.assertEqual(calc_author_name_key(u'Zoë smith'), calc_author_name_key(u'Zoe smith'))

    def test_different_umlauts_of_author_name_do_not_matter(self):
        self.assertNotEqual(calc_author_name_key(u'jøn smith'), calc_author_name_key(u'jën smith'))

    def test_other_punctuation_does_not_matter(self):
        self.assertEqual(calc_author_name_key(u'j_:-smith'), calc_author_name_key(u'j smith'))



if __name__ == '__main__':
    unittest.main()

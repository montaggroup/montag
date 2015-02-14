import unittest
import pydb

import logging
logger = logging.getLogger('test_tome_add')

import os
import helpers


logging.basicConfig(level=logging.WARN)


def get_schema_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'db-schemas'))


class TestAddTome(unittest.TestCase):
    def setUp(self):
        self.main_db = helpers.build_main_db_memory_only(get_schema_dir())

    def test_adding_an_tome_generates_a_tome_id_with_which_we_can_fetch_the_tome_again(self):
        author_id = self.main_db.add_author(name='john smith')

        tome_id = self.main_db.add_tome('ti', 'lang', [author_id])
        tome = self.main_db.get_tome(tome_id)

        self.assertIsNotNone(tome)
        self.assertEqual(tome['title'], 'ti')
        self.assertEqual(tome['principal_language'], 'lang')


class TestFindOrCreateTome(unittest.TestCase):
    def setUp(self):
        self.main_db = helpers.build_main_db_memory_only(get_schema_dir())
        self.author_id = self.main_db.add_author(name='john smith')

    def _add_tome(self, tome_type=pydb.TomeType.Fiction,
                  title='ti', subtitle='subt', edition='edi',
                  publication_year=2010, author_ids=None):
        """
        :type edition: string or unicode or None
        :type publication_year: string or unicode or int or None
        """
        if author_ids is None:
            author_ids = [self.author_id]

        return self.main_db.find_or_create_tome(title, 'lang', author_ids, subtitle=subtitle,
                                                tome_type=tome_type, fidelity=55.0,
                                                edition=edition, publication_year=publication_year)

    def test_find_or_create_tome_creates_a_new_tome_if_db_is_empty(self):
        tome_id = self._add_tome()
        tome = self.main_db.get_tome(tome_id)

        self.assertIsNotNone(tome)
        self.assertEqual(tome['title'], 'ti')
        self.assertEqual(tome['subtitle'], 'subt')
        self.assertEqual(tome['principal_language'], 'lang')
        self.assertEqual(tome['fidelity'], 55.0)

    def test_find_or_create_tome_will_not_create_the_same_tome_again(self):
        tome_id_1 = self._add_tome()
        tome_id_2 = self._add_tome()

        self.assertEqual(tome_id_1, tome_id_2)

    def test_find_or_create_tome_will_create_a_new_tome_if_title_differs(self):
        tome_id_1 = self._add_tome()
        tome_id_2 = self._add_tome(title='new title')
        self.assertNotEqual(tome_id_1, tome_id_2)

    def test_find_or_create_tome_will_create_a_new_tome_if_subtitle_differs(self):
        tome_id_1 = self._add_tome()
        tome_id_2 = self._add_tome(subtitle='new subtitle')
        self.assertNotEqual(tome_id_1, tome_id_2)

    def test_find_or_create_tome_will_create_a_new_tome_if_author_differs(self):
        tome_id_1 = self._add_tome()
        author_id_2 = self.main_db.add_author(name='jack smith')

        tome_id_2 = self._add_tome(author_ids=[author_id_2])
        self.assertNotEqual(tome_id_1, tome_id_2)

    def test_find_or_create_tome_will_create_a_new_tome_if_edition_differs(self):
        tome_id_1 = self._add_tome()
        tome_id_2 = self._add_tome(edition='new ed')
        self.assertNotEqual(tome_id_1, tome_id_2)

    def test_find_or_create_tome_will_create_a_new_tome_if_pubyear_differs(self):
        tome_id_1 = self._add_tome(publication_year=1975)
        tome_id_2 = self._add_tome(publication_year=1976)
        self.assertNotEqual(tome_id_1, tome_id_2)

    def test_find_or_create_tome_not_create_a_new_tome_if_type_differs(self):
        tome_id_1 = self._add_tome()
        tome_id_2 = self._add_tome(tome_type=pydb.TomeType.NonFiction)
        self.assertEqual(tome_id_1, tome_id_2)

    def test_in_the_presence_of_a_specific_tome_find_or_create_will_use_the_generic_tome_if_new_tome_is_generic(self):
        tome_id_1 = self._add_tome(edition=None)
        tome_id_2_specific = self._add_tome(edition='spec')
        tome_id_3 = self._add_tome(edition=None)

        self.assertNotEqual(tome_id_1, tome_id_2_specific)
        self.assertEqual(tome_id_1, tome_id_3)

    def in_the_presence_of_a_specific_tome_find_or_create_will_use_that_one_if_new_tome_is_generic_edition_case(self):
        tome_id_1 = self._add_tome(edition="first edition")
        tome_id_2 = self._add_tome(edition=None)

        self.assertEqual(tome_id_1, tome_id_2)

    def in_the_presence_of_a_specific_tome_find_or_create_will_use_that_one_if_new_tome_is_generic_pubyear_case(self):
        tome_id_1 = self._add_tome(publication_year=1975)
        tome_id_2 = self._add_tome(publication_year=None)

        self.assertEqual(tome_id_1, tome_id_2)




if __name__ == '__main__':
    unittest.main()

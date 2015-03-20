import unittest

import pydb.localdb as localdb
import pydb.testing.unittests


class TestAddTome(unittest.TestCase):
    def setUp(self):
        self.local_db = localdb.LocalDB(":memory:", pydb.testing.guess_schema_path(), enable_db_sync=False)

    def test_add_tome_with_the_same_author_id_twice_leads_to_the_author_link_added_only_once(self):
        l = self.local_db

        new_tome_id = l.add_tome(guid='aa', title='bb', principal_language='en', author_ids=[1, 1],
                                 fidelity=70, publication_year=1970, edition='first',
                                 subtitle='sub title', tome_type=1)

        linked_author_ids = l.get_tome_author_ids(new_tome_id)
        self.assertEqual(linked_author_ids, [1])


if __name__ == '__main__':
    unittest.main()

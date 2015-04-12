import unittest
import service_helpers
import web2py_helpers
import database_helpers
import pydb.pyrosetup

web2py_helpers.prepare_web2py()


class TestRandomTomes(unittest.TestCase):
    def setUp(self):
        self.random_tomes = web2py_helpers.build_request('default', 'random_tomes')
        service_helpers.start_services(self.id())

    def tearDown(self):
        service_helpers.stop_services()

    def test_having_an_empty_database_random_tomes_returns_list_and_view_renders(self):
        res = self.random_tomes.execute()
        self.assertIn('tome_info', res)
        tome_info = res['tome_info']
        self.assertEqual(len(tome_info), 0)

        html = self.random_tomes.render_result()
        self.assertIn('Random ', html)

    def test_having_an_database_with_one_entry_random_tomes_returns_list_and_view_renders(self):
        db = pydb.pyrosetup.pydbserver()

        author = database_helpers.add_sample_author(db)
        database_helpers.add_sample_tome(db, author['id'])
        res = self.random_tomes.execute()
        self.assertIn('tome_info', res)
        tome_info = res['tome_info']
        self.assertEqual(len(tome_info), 1)

        html = self.random_tomes.render_result()
        self.assertIn('Random ', html)


if __name__ == '__main__':
    unittest.main()

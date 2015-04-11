import unittest
import service_helpers
import web2py_helpers

web2py_helpers.prepare_web2py()


class TestRandomTomes(unittest.TestCase):
    def setUp(self):
        self.random_tomes = web2py_helpers.build_request('default', 'random_tomes')
        service_helpers.start_services()

    def tearDown(self):
        service_helpers.stop_services()

    def test_empty_database_random_tomes_returns_list_and_view_renders(self):
        res = self.random_tomes.execute()
        self.assertIn('tome_info', res)

        html = self.random_tomes.render_result()
        self.assertIn('Random ', html)

if __name__ == '__main__':
    unittest.main()

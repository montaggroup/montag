# coding=utf-8
import unittest
import service_helpers
import web2py_helpers
import pydb.testing

web2py_helpers.prepare_web2py()


class TestTomeSearch(unittest.TestCase):
    def setUp(self):
        tc_folder = pydb.testing.get_clean_testcase_folder(self.id())
        self.tomesearch = web2py_helpers.build_request(tc_folder, 'default', 'tomesearch')
        service_helpers.start_services(tc_folder)

    def tearDown(self):
        service_helpers.stop_services()

    def test_opening_search_form_returns_a_form_element_and_view_renders(self):
        res = self.tomesearch.execute()
        self.assertIn('form', res)

        html = self.tomesearch.render_result()
        self.assertIn('<form ', html)

    def test_executed_search_from_returns_a_result_list_and_view_renders(self):
        self.tomesearch.add_get_vars({
            '_formname': 'search',
            'query': 'hello',
            'principal_language': '',
            'tome_type': '2'
        })
        res = self.tomesearch.execute()
        self.assertIn('tome_info', res)

        html = self.tomesearch.render_result()
        self.assertIn('Results for hello', html)


if __name__ == '__main__':
    unittest.main()

import unittest
import pydb.pyrosetup

import service_helpers
import web2py_helpers
web2py_helpers.prepare_web2py()


class TestEditAuthor(unittest.TestCase):
    def setUp(self):
        self.edit_author = web2py_helpers.build_request('default', 'edit_author')
        service_helpers.start_services(self.id())
        self.pdb = pydb.pyrosetup.pydbserver()

    def tearDown(self):
        service_helpers.stop_services()

    def test_edit_author_returns_form_and_view_renders(self):
        author_id = self.pdb.add_author('john doe')
        db_author = self.pdb.get_author(author_id)
        author_guid = db_author['guid']

        self.edit_author.add_args(author_guid)
        res = self.edit_author.execute()

        self.assertIn('author', res)
        author_data = res['author']
        self.assertEqual(author_data['name'], 'john doe')

        html = self.edit_author.render_result()
        self.assertIn('john doe', html)


if __name__ == '__main__':
    unittest.main()

# coding=utf-8
import unittest
import service_helpers
import web2py_helpers
import pydb.pyrosetup
import database_helpers
web2py_helpers.prepare_web2py()


class TestViewTome(unittest.TestCase):
    def setUp(self):
        tc_folder = pydb.testing.get_clean_testcase_folder(self.id())
        self.view_tome = web2py_helpers.build_request(tc_folder, 'default', 'view_tome')
        service_helpers.start_services(tc_folder, fileserver=True)
        self.pdb = pydb.pyrosetup.pydbserver()

    def tearDown(self):
        service_helpers.stop_services()

    def test_view_tome_with_a_tome_having_a_file_returns_correct_author_and_view_renders(self):
        author_id = self.pdb.add_author('viewmaster')
        tome = database_helpers.add_sample_tome(self.pdb, author_id, upload_a_file=True)
        tome_guid = tome['guid']

        self.view_tome.add_args(tome_guid)
        res = self.view_tome.execute()
        self.assertIn('tome', res)
        result_tome = res['tome']

        self.assertIn('authors', result_tome)
        authors = result_tome['authors']
        self.assertEqual(len(authors), 1)
        result_author = authors[0]
        self.assertIn('detail', result_author)
        self.assertEqual(result_author['detail']['name'], 'viewmaster')

        html = self.view_tome.render_result()
        self.assertIn('viewmaster', html)

    def test_view_tome_with_a_tome_having_private_tag_returns_the_tag_and_view_renders(self):
        author_id = self.pdb.add_author('viewmaster')
        tome = database_helpers.add_sample_tome(self.pdb, author_id, upload_a_file=True, tag_values=["%secret"])
        tome_guid = tome['guid']

        self.view_tome.add_args(tome_guid)
        res = self.view_tome.execute()
        self.assertIn('tome', res)
        result_tome = res['tome']

        self.assertIn('tags', result_tome)
        tags = result_tome['tags']
        self.assertEqual(len(tags), 3)

        private_tag_values = [tag['tag_value'] for tag in tags if tag['tag_value'].startswith('%')]
        self.assertEqual(private_tag_values, ['%secret'])

        html = self.view_tome.render_result()
        self.assertIn('%secret', html)

if __name__ == '__main__':
    unittest.main()

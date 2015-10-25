import unittest
import pydb.pyrosetup

import service_helpers
import web2py_helpers
web2py_helpers.prepare_web2py()


class TestEditTome(unittest.TestCase):
    def setUp(self):
        tc_folder = pydb.testing.get_clean_testcase_folder(self.id())
        self.edit_tome = web2py_helpers.build_request(tc_folder, 'default', 'edit_tome')
        service_helpers.start_services(tc_folder)
        self.pdb = pydb.pyrosetup.pydbserver()

    def tearDown(self):
        service_helpers.stop_services()

    def test_edit_tome_returns_form_and_view_renders(self):
        author_id = self.pdb.add_author('gragra')
        tome_id = self.pdb.add_tome(title='there must be memories', principal_language='en', author_ids=[author_id])
        self.pdb.add_tags_to_tome(tome_id, ['hi-fi-tag'], 80.0)
        self.pdb.add_tags_to_tome(tome_id, ['lo-fi-tag'], 10.0)
        self.pdb.add_tags_to_tome(tome_id, ['neg-fi-tag'], -80.0)
        db_tome = self.pdb.get_tome(tome_id)
        tome_guid = db_tome['guid']

        self.edit_tome.add_args(tome_guid)
        res = self.edit_tome.execute()

        self.assertIn('tome', res)
        tome_data = res['tome']
        self.assertEqual(tome_data['title'], 'there must be memories')

        html = self.edit_tome.render_result()
        # the title should be visible
        self.assertIn('there must be memories', html)
        # the only author should be visible
        self.assertIn('gragra', html)
        # high fidelity tags are part of the tome view -> should be visible
        self.assertIn('hi-fi-tag', html)
        # negative high fidelity tags are part of the opinion -> should be visible for editing
        self.assertIn('neg-fi-tag', html)
        # low fidelity tags are not part of of the opinion -> should not be visible for editing
        self.assertNotIn('lo-fi-tag', html)


if __name__ == '__main__':
    unittest.main()

import unittest
import service_helpers
import web2py_helpers
import pydb.pyrosetup
from pydb.testing import test_data
from pydb import FileType

web2py_helpers.prepare_web2py()


class TestViewTome(unittest.TestCase):
    def setUp(self):
        self.view_tome = web2py_helpers.build_request('default', 'view_tome')
        service_helpers.start_services(fileserver=True)
        self.pdb = pydb.pyrosetup.pydbserver()

    def tearDown(self):
        service_helpers.stop_services()

    def test_view_tome_with_a_tome_having_a_file_returns_correct_author_and_view_renders(self):
        author_id = self.pdb.add_author('viewmaster')
        tome_id = self.pdb.add_tome(title='it is also on file!', principal_language='en', author_ids=[author_id],
                                    tags_values=['one tag', 'two tag'])
        tome = self.pdb.get_tome(tome_id)
        tome_guid = tome['guid']

        file_path = test_data.get_book_path('pg1661.epub')

        (file_id, file_hash, size) = pydb.pyrosetup.fileserver().add_file_from_local_disk(file_path, 'epub',
                                                                                          move_file=False)

        self.pdb.link_tome_to_file(tome_id, file_hash, size, file_extension='epub', file_type=FileType.Content,
                                   fidelity=80)

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

if __name__ == '__main__':
    unittest.main()

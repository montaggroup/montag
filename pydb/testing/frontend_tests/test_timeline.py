import unittest
import service_helpers
import web2py_helpers
import pydb.pyrosetup
from pydb.testing import test_data
from pydb import FileType

web2py_helpers.prepare_web2py()


class TestTimeLine(unittest.TestCase):
    def setUp(self):
        self.timeline = web2py_helpers.build_request('default', 'timeline')
        service_helpers.start_services(fileserver=True)
        self.pdb = pydb.pyrosetup.pydbserver()

    def tearDown(self):
        service_helpers.stop_services()

    def test_empty_timeline_returns_list_and_view_renders(self):
        res = self.timeline.execute()
        self.assertIn('tome_info', res)

        html = self.timeline.render_result()
        self.assertIn('Timeline', html)

    def test_timeline_with_a_tome_having_a_file_returns_list_and_view_renders(self):

        author_id = self.pdb.add_author('filemaster')
        tome_id = self.pdb.add_tome(title='it is on file!', principal_language='en', author_ids=[author_id])
        file_path = test_data.get_book_path('pg1661.epub')

        (file_id, file_hash, size) = pydb.pyrosetup.fileserver().add_file_from_local_disk(file_path, 'epub',
                                                                                          move_file=False)

        self.pdb.link_tome_to_file(tome_id, file_hash, size, file_extension='epub', file_type=FileType.Content,
                                   fidelity=80)

        res = self.timeline.execute()
        self.assertIn('tome_info', res)
        tome_info = res['tome_info']
        self.assertGreaterEqual(len(tome_info), 1)

        html = self.timeline.render_result()
        self.assertIn('Timeline', html)

    def test_timeline_with_a_tome_having_two_tags_returns_list_and_view_renders(self):
        author_id = self.pdb.add_author('tagmaster')
        self.pdb.add_tome(title='tig tag toe!', principal_language='en', author_ids=[author_id],
                          tags_values=['one tag', 'two tag'])

        res = self.timeline.execute()
        self.assertIn('tome_info', res)
        tome_info = res['tome_info']
        self.assertGreaterEqual(len(tome_info), 1)

        html = self.timeline.render_result()
        self.assertIn('two tag', html)

if __name__ == '__main__':
    unittest.main()

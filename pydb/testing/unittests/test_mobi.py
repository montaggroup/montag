import unittest
import cStringIO
from pydb.ebook_metadata_tools import mobi


class TestMobiAddMetaData(unittest.TestCase):
    def test_empty_stream_results_in_value_error(self):
        input = cStringIO.StringIO('')
        output = cStringIO.StringIO()
        tome = {'title': 'a tome', 'subtitle': None}
        tome_file = {'hash': 'dedededededede'}
        with self.assertRaises(ValueError):
            mobi.add_metadata(input, output, [], tome, tome_file)


if __name__ == '__main__':
    unittest.main()

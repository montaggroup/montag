import unittest
import io
from pydb.ebook_metadata_tools import mobi


class TestMobiAddMetaData(unittest.TestCase):
    def test_empty_stream_results_in_value_error(self):
        input_ = io.StringIO('')
        output = io.StringIO()
        tome = {'title': 'a tome', 'subtitle': None}
        tome_file = {'hash': 'dedededededede'}
        with self.assertRaises(ValueError):
            mobi.add_metadata(input_, output, [], tome, tome_file)


if __name__ == '__main__':
    unittest.main()

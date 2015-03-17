import unittest
import os
import pydb.ebook_metadata_tools as etools
from pydb.testing.integration_tests import get_testdata_path

script_path = os.path.dirname(__file__)
epub_file_path = get_testdata_path('pg1661.epub')
txt_file_path = get_testdata_path('pg1661.txt')


def extract_cover_from_file(file_path, extension):
    with open(file_path, 'rb') as source_stream:
        return etools.get_cover_image(source_stream, 'epub')


class TestCoverExtraction(unittest.TestCase):
    def test_epub_without_cover_leads_to_none(self):
        result = extract_cover_from_file(txt_file_path, 'txt')
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()

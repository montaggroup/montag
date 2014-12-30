import unittest
import pydb.ebook_metadata_tools.epub as epub


good_sample = """<?xml version="1.0" encoding="utf-8" standalone="no"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="12345" version="2.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
      <dc:title>some title</dc:title>
      <dc:creator>some body</dc:creator>
      <dc:date>1999-09-09</dc:date>
      <dc:language>en</dc:language>
  </metadata>
  <manifest/>
  <spine/>
  <guide/>
</package>
"""

date_broken_sample = """<?xml version="1.0" encoding="utf-8" standalone="no"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="12345" version="2.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
      <dc:creator>some body</dc:creator>
      <dc:date>199</dc:date>
  </metadata>
  <manifest/>
  <spine/>
  <guide/>
</package>
"""


class test_epub_get_metadata(unittest.TestCase):
    def test_empty_of_does_not_lead_to_error(self):
        epub.get_metadata_from_opf_string("")

    def test_single_author_is_extracted_correctly(self):
        result = epub.get_metadata_from_opf_string(good_sample)
        self.assertEqual(len(result['author_names']), 1)
        self.assertEqual(result['author_names'][0], 'some body')

    def test_date_is_extracted_correctly(self):
        result = epub.get_metadata_from_opf_string(good_sample)
        self.assertEqual(int(result['publication_year']), 1999)


    def test_date_without_year_does_not_lead_to_error(self):
        result = epub.get_metadata_from_opf_string(date_broken_sample)
        self.assertEqual(len(result['author_names']), 1)
        self.assertEqual(result['author_names'][0], 'some body')
        self.assertNotIn('publication_year', result)


if __name__ == '__main__':
    unittest.main()

import unittest
import pydb.opf
import re,os
import tempfile


class TestOpfOperations(unittest.TestCase):
    def setUp(self):
        self.metadata = pydb.opf.Metadata()
        self.metadata.title = "a title for test"
        self.metadata.authors = ["one author", "another author"]
        self.metadata.series = "a series for tests!"
        self.metadata.series_index = "451"
        self.metadata.title_sort = "title for test, a"
        self.metadata.tags = ["tag1", "tag team"]
        self.metadata.language = "en"

        self.reference_opf_string=\
            """<?xml version='1.0' encoding='utf-8'?>
               <package xmlns="http://www.idpf.org/2007/opf" unique-identifier="uuid_id">
                   <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
                       <dc:identifier opf:scheme="opf" id="opf_id">123</dc:identifier>
                       <dc:identifier opf:scheme="uuid" id="uuid_id">123</dc:identifier>
                       <dc:title>a title for test</dc:title>
                       <dc:language>en</dc:language>
                       <dc:creator opf:role="aut">one author</dc:creator>
                       <dc:creator opf:role="aut">another author</dc:creator>
                       <meta content="a series for tests!" name="calibre:series"/>
                       <meta content="451" name="calibre:series_index"/>
                       <meta content="title for test, a" name="calibre:title_sort"/>
                       <dc:subject>tag1</dc:subject>
                       <dc:subject>tag team</dc:subject>
                   </metadata>
                   <guide/>
               </package>"""

        pass

    def _is_metadata_correct(self, metadata):
        self.assertEquals(metadata.title, "a title for test")
        self.assertEquals(metadata.authors, ["one author", "another author"])
        self.assertEquals(metadata.series, "a series for tests!")
        self.assertEquals(metadata.series_index, "451")
        self.assertEquals(metadata.title_sort, "title for test, a")
        self.assertEquals(metadata.tags, ["tag1", "tag team"])

    def test_create_metadata_object_from_code(self):
        mi = pydb.opf.Metadata()

        mi.title = "a title for test"
        mi.authors = ["one author", "another author"]
        mi.series = "a series for tests!"
        mi.series_index = "451"
        mi.title_sort = "title for test, a"
        mi.tags = ["tag1", "tag team"]
        mi.language = "en"

        self.assertTrue(mi)
        self._is_metadata_correct(mi)

    def test_reading_metadata_from_file(self):
        fd,filename = tempfile.mkstemp()
        os.write(fd, self.reference_opf_string)
        os.close(fd)

        metadata = pydb.opf.Metadata.from_file(filename)

        self.assertTrue(metadata)
        self._is_metadata_correct(metadata)



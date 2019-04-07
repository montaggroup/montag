# coding=utf-8
import unittest
from pydb import opf
import os
import tempfile


class TestOpfOperations(unittest.TestCase):
    def setUp(self):
        self.reference_opf_string = \
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
                       <dc:date opf:event="original-publication">2012-09-10</dc:date>
                   </metadata>
                   <guide/>
               </package>"""

        pass

    def _assert_is_metadata_correct(self, metadata):
        self.assertEquals(metadata.title, "a title for test")
        self.assertEquals(metadata.authors, ["one author", "another author"])
        self.assertEquals(metadata.series, "a series for tests!")
        self.assertEquals(metadata.series_index, "451")
        self.assertEquals(metadata.title_sort, "title for test, a")
        self.assertEquals(metadata.tags, ["tag1", "tag team"])
        self.assertEquals(metadata.publication_year, 2012)

    def test_reading_metadata_from_file(self):
        fd, filename = tempfile.mkstemp(prefix = 'pydb_test_opf')
        os.write(fd, self.reference_opf_string)
        os.close(fd)

        metadata = opf.read_metadata_from_file(filename)

        self.assertTrue(metadata)
        self._assert_is_metadata_correct(metadata)


class TestOpfReadBack(unittest.TestCase):
    def setUp(self):
        self.md = opf.Metadata()

    def test_read_back_edition(self):
        self.md.edition = 'my edition'
        xml = self.md.to_opf_string()
        print xml

        read_back = opf.read_metadata_from_string(xml)
        self.assertEqual(read_back.edition, 'my edition')

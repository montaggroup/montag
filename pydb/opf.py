#!/usr/bin/python

import logging
import re
import defusedxml

logger = logging.getLogger('opf')


DC11_NS = 'http://purl.org/dc/elements/1.1/'
OPF2_NS = 'http://www.idpf.org/2007/opf'
APP_NAME = "opf"


def opf(name):
    return '{%s}%s' % (OPF2_NS, name)


def dc(name):
    return '{%s}%s' % (DC11_NS, name)


class Metadata:
    def __init__(self):
        self.title = ""
        self.authors = []
        self.series = ""
        self.series_index = None
        self.title_sort = ""
        self.language = "en"
        self.tags = []

        logger.info("opf inititalized")

    @classmethod
    def from_file(cls, filename):
        import defusedxml.ElementTree as ET #use hardened xml implementation because reading unknown xml document

        def clean_string(string):
            string = string.strip()
            string = re.sub("  +", " ", string)
            return string


        #parser = etree.XMLParser(ns_clean=True)
        #tree = etree.parse(filename, parser)
        #root = tree.getroot()
        tree = ET.parse(filename)
        root = tree.getroot()
        result = cls()
        for child in root:
            #print child.tag
            if child.tag.endswith('metadata'):
                for meta in child:
                    logger.debug("%s %s %s", meta.tag, meta.attrib, meta.text)
                    if meta.text:
                        text = clean_string(meta.text)
                    if meta.tag.endswith('title'):
                        result.title = text
                    elif meta.tag.endswith('language'):
                        result.language = text
                    elif meta.tag.endswith('creator'):
                        result.authors.append(text)
                    elif meta.tag.endswith('subject'):
                        result.tags.append(text)
                    elif meta.tag.endswith('meta'):
                        attrib = meta.attrib['name']
                        if attrib == 'calibre:title_sort':
                            result.title_sort = clean_string(meta.attrib['content'])
                        elif attrib == 'calibre:series':
                            result.series = clean_string(meta.attrib['content'])
                        elif attrib == 'calibre:series_index':
                            result.series_index = clean_string(meta.attrib['content'])

        return result

    def __str__(self):
        series_text = ""
        if self.series_index:
            series_text = " Part %d of series %s" % (self.series_index, self.series)

        return "Metadata: %s by %s Language: %s Tags: %s" % (
            self.title, "; ".join(self.authors), self.language, self.tags) + series_text

if __name__ == "__main__":
    mi = Metadata()

    mi.title = "a title"
    mi.authors = ["one author", "another author"]
    mi.series = "a series!"
    mi.series_index = 12
    mi.title_sort = "title, a"
    mi.tags = ["EXAMPLEs", "bad examples"]

    print mi

    opf_text = mi.to_opf(True)

    print opf_text


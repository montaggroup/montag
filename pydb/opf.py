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
        #from lxml import etree
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

    def to_opf(self, as_string=True):
        import xml.etree.ElementTree as ET #use standard xml library because writing and register_namespace is present
        from lxml import etree
        import textwrap
        import StringIO

        #root = etree.fromstring(textwrap.dedent(
        tree = ET.parse(StringIO.StringIO(textwrap.dedent(
            '''
            <package xmlns="http://www.idpf.org/2007/opf" unique-identifier="uuid_id">
                <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
                    <dc:identifier opf:scheme="%(a)s" id="%(a)s_id">%(id)s</dc:identifier>
                    <dc:identifier opf:scheme="uuid" id="uuid_id">%(uuid)s</dc:identifier>
                    </metadata>
                <guide/>
            </package>
            ''' % dict(a=APP_NAME, id=123, uuid=123))))
        root = tree.getroot()
        metadata = root[0]
        metadata[0].tail = '\n' + (' ' * 8)

        def factory(tag_name, text=None, sort=None, role=None, scheme=None, name=None,
                    content=None):
            attrib = {}
            if sort:
                attrib[opf('file-as')] = sort
            if role:
                attrib[opf('role')] = role
            if scheme:
                attrib[opf('scheme')] = scheme
            if name:
                attrib['name'] = name
            if content:
                attrib['content'] = content
            elem = metadata.makeelement(tag_name, attrib=attrib)
            elem.tail = '\n' + (' ' * 8)
            if text:
                try:
                    elem.text = text.strip()
                except ValueError:
                    logger.error("Failed to strip %s", text)
                    # elem.text = clean_ascii_chars(text.strip())
            metadata.append(elem)

        factory(dc('title'), self.title)
        factory(dc('language'), self.language)
        for au in self.authors:
            factory(dc('creator'), au, None, 'aut')
        meta = lambda n, c: factory('meta', name='calibre:' + n, content=c)
        if self.series:
            meta('series', self.series)
        if self.series_index is not None:
            meta('series_index', str(self.series_index))
        if self.title_sort:
            meta('title_sort', self.title_sort)

        for tag in self.tags:
            factory(dc('subject'), tag)

        metadata[-1].tail = '\n' + (' ' * 4)

        ET.register_namespace('', 'xmlns:opf="http://www.idpf.org/2007/opf')
        if as_string:
            string_file = StringIO.StringIO()
            tree.write(file_or_filename=string_file,encoding='utf-8',xml_declaration=True)
            return string_file.getvalue()
        return root
        #return (ET.tostring(element=root,encoding='utf-8',xml_declaration=True)) if as_string else root
        #return etree.tostring(root, pretty_print=True, encoding='utf-8',
        #                      xml_declaration=True) if as_string else root

    def write_opf_to_file(self, filename):
        text = self.to_opf()
        with open(filename, 'wb') as f:
            f.write(text)


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


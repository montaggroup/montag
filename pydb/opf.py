#!/usr/bin/python

import logging
import re
import defusedxml.ElementTree as ET  # use hardened xml implementation because reading unknown xml document

logger = logging.getLogger('opf')

DC11_NS = 'http://purl.org/dc/elements/1.1/'
OPF2_NS = 'http://www.idpf.org/2007/opf'
APP_NAME = "opf"


class Metadata(object):
    def __init__(self):
        self.title = None
        self.authors = []
        self.series = None
        self.series_index = None
        self.title_sort = None
        self.language = "en"
        self.tags = []
        self.publication_year = None
        self.edition = None

        logger.debug("opf initialized")

    def __str__(self):
        series_text = ""
        if self.series_index:
            series_text = " Part %d of series %s" % (self.series_index, self.series)

        return "Metadata: %s by %s Language: %s Tags: %s" % (
            self.title, "; ".join(self.authors), self.language, self.tags) + series_text

    def to_opf_string(self):
        from lxml import etree  # can do pretty printing

        root = etree.fromstring("""
                <package xmlns="http://www.idpf.org/2007/opf" unique-identifier="uuid_id">
                    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
                    </metadata>
                    <guide/>
                </package>
                """)
        metadata_element = root[0]

        def add_tag(tag_name, text=None, sort=None, role=None, scheme=None, name=None, content=None):
            attrib = {}
            if sort is not None:
                attrib[_opf_ns('file-as')] = sort
            if role is not None:
                attrib[_opf_ns('role')] = role
            if scheme is not None:
                attrib[_opf_ns('scheme')] = scheme
            if name is not None:
                attrib['name'] = name
            if content is not None:
                attrib['content'] = content
            elem = metadata_element.makeelement(tag_name, attrib=attrib)
            if text is not None:
                elem.text = text.strip()
            metadata_element.append(elem)

        add_tag(_dc_ns('title'), self.title)
        add_tag(_dc_ns('language'), self.language)

        for au in self.authors:
            add_tag(_dc_ns('creator'), au, role='aut')

        if self.series is not None:
            add_tag('meta', name='calibre:series', content=self.series)
        if self.series_index is not None:
            add_tag('meta', name='calibre:series_index', content=str(self.series_index))
        if self.title_sort is not None:
            add_tag('meta', name='calibre:title_sort', content=self.title_sort)
        if self.edition is not None:
            add_tag('meta', name='pydb:edition_name', content=self.edition)

        for tag in self.tags:
            add_tag(_dc_ns('subject'), tag)

        return etree.tostring(root, pretty_print=True, encoding='utf-8', xml_declaration=True)

    def write_to_file(self, filename):
        text = self.to_opf_string()
        with open(filename, 'w') as f:
            f.write(text)


def read_metadata_from_file(filename):
    with open(filename) as f:
        xml = f.read()

    return read_metadata_from_string(xml)


def read_metadata_from_string(xml):
    root = ET.fromstring(xml)

    result = Metadata()
    for child in root:
        if child.tag.endswith('metadata'):
            for meta_element in child:
                _parse_meta_element(meta_element, result)
    return result


def _parse_meta_element(element, metadata):
    logger.debug("%s %s %s", element.tag, element.attrib, element.text)
    if element.text:
        text = _clean_string(element.text)
        if element.tag.endswith('title'):
            metadata.title = text
        elif element.tag.endswith('language'):
            metadata.language = text
        elif element.tag.endswith('creator'):
            metadata.authors.append(text)
        elif element.tag.endswith('subject'):
            metadata.tags.append(text)
        elif element.tag.endswith('date'):
            year_match = re.match("([0-9]{4}).*", text)
            if year_match:
                metadata.publication_year = int(year_match.group(1))
    elif element.tag.endswith('meta'):
        attrib = element.attrib['name']
        if attrib == 'calibre:title_sort':
            metadata.title_sort = _clean_string(element.attrib['content'])
        elif attrib == 'calibre:series':
            metadata.series = _clean_string(element.attrib['content'])
        elif attrib == 'calibre:series_index':
            metadata.series_index = _clean_string(element.attrib['content'])
        elif attrib == 'pydb:edition_name':
            metadata.edition = _clean_string(element.attrib['content'])


def _opf_ns(name):
    return '{%s}%s' % (OPF2_NS, name)


def _dc_ns(name):
    return '{%s}%s' % (DC11_NS, name)


def _clean_string(string):
    string = string.strip()
    string = re.sub("  +", " ", string)
    return string

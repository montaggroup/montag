import pydb.zipfile.zipfile as zipfile
import xml.etree.ElementTree as etree
import defusedxml.ElementTree as defused_etree
import re
import logging
from pydb import title
import zlib

logger = logging.getLogger('epub')
logger.addHandler(logging.NullHandler())

etree.register_namespace("", "http://www.idpf.org/2007/opf")


def _get_path_of_content_opf(zip_file):
    try:
        ocf_metadata = zip_file.read("META-INF/container.xml")
    except KeyError:
        raise ValueError("Unable to find META-INF/container.xml in epub file")
    root = defused_etree.fromstring(ocf_metadata)
    rootfiletag = root.find(".//*[@full-path]")
    content_opf_path = rootfiletag.attrib['full-path']
    # logger.debug("content file is at" % content_opf_path)
    return content_opf_path


def _read_content_opf(zip_file, filename):
    return zip_file.read(filename)


def _write_content_opf(zip_file, filename, opf_contents):
    zi = zipfile.ZipInfo(filename, (2012, 6, 5, 4, 51, 0))
    zi.compress_type = zipfile.ZIP_STORED
    zip_file.writestr(zi, opf_contents)


def _copy_zip_contents(inzip, outzip, filenames_to_skip=list()):
    for item in inzip.infolist():
        # logger.debug("Copying %s" % item.filename)
        contents = inzip.read(item.filename)
        if item.filename not in filenames_to_skip:
            outzip.writestr(item, contents)
        else:
            logger.debug("Skipped copy of %s" % item.filename)


def clear_metadata(instream, outstream):
    try:
        with zipfile.ZipFile(instream, 'r') as inzip:
            opf_path = _get_path_of_content_opf(inzip)
            opf_content = _read_content_opf(inzip, opf_path)

            removed_a_node = False
            try:
                root = defused_etree.fromstring(opf_content)
                for main_element in root:
                    logger.debug("main el %s " % main_element.tag)
                    if re.match(".*metadata$", main_element.tag):
                        logger.debug("Found metadata tag, cleaning")

                        while list(main_element):  # do not remove using a for loop
                            # - this will skip elements in python 2.7.5!
                            node_to_remove = list(main_element)[0]
                            logger.debug("Removing node %s" % node_to_remove.tag)
                            main_element.remove(node_to_remove)
                            removed_a_node = True
            except defused_etree.ParseError, e:
                logger.error("Caught a parse error while trying to clear epub metadata: %s" % repr(e))
                raise ValueError("Invalid EPUB syntax")

            if removed_a_node:
                logger.debug("Writing a new epub file")
                with zipfile.ZipFile(outstream, 'w') as outzip:
                    try:
                        _copy_zip_contents(inzip, outzip, [opf_path])
                    except zipfile.BadZipfile, e:
                        raise ValueError("Caught a BadZipFile exception: %s" % repr(e))

                    new_content = etree.tostring(root)
                    _write_content_opf(outzip, opf_path, new_content)
    except zipfile.BadZipfile:
        raise ValueError("Unable to open epub zip")
    except KeyError:
        raise ValueError("Could not find all required files in epub")
    except zlib.error:
        raise ValueError("Zliberror in zip file")
    except RuntimeError:
        raise ValueError("zipfile required password")

    if not removed_a_node:  # don't re-zip of nothing changed
        logger.debug("Nothing changed")
        instream.seek(0)
        outstream.write(instream.read())
        outstream.close()

    return True


def add_metadata(instream, outstream, author_docs, tome_doc, tome_file):
    try:
        with zipfile.ZipFile(instream, 'r') as inzip:
            opf_path = _get_path_of_content_opf(inzip)
            opf_content = _read_content_opf(inzip, opf_path)

            root = defused_etree.fromstring(opf_content)
            for main_element in root:
                logger.debug("main el %s" % main_element.tag)
                if re.match(".*metadata$", main_element.tag):
                    logger.debug("Found metadata tag, cleaning")

                    while list(main_element):  # do not remove using a for loop - this will skip elements in python 2.7.5!
                        node_to_remove = list(main_element)[0]
                        logger.debug("Removing node %s" % node_to_remove.tag)
                        main_element.remove(node_to_remove)

                    for author_doc in author_docs:
                        author_el = etree.SubElement(main_element, "{http://purl.org/dc/elements/1.1/}creator",
                                                     {"{http://www.idpf.org/2007/opf}role": "aut"})
                        author_el.text = author_doc['name']
                    title_el = etree.SubElement(main_element, "{http://purl.org/dc/elements/1.1/}title")
                    title_el.text = title.coalesce_title(tome_doc['title'], tome_doc['subtitle'])
                    language_el = etree.SubElement(main_element, "{http://purl.org/dc/elements/1.1/}language")
                    language_el.text = tome_doc['principal_language']
                    # \todo more tags, e.g. file hash in relation or tome guid in source

            with zipfile.ZipFile(outstream, 'w') as outzip:
                _copy_zip_contents(inzip, outzip, [opf_path])

                new_content = etree.tostring(root)
                _write_content_opf(outzip, opf_path, new_content)
    except zipfile.BadZipfile:
        raise ValueError("Unable to open epub zip")

    instream.seek(0)
    return True


def get_metadata_from_opf_string(opf_content):
    result = {'author_names': []}

    def clean_string(string):
        if string is None:
            return None
        string = re.sub('  +', ' ', string)
        return string.strip()

    try:
        root = defused_etree.fromstring(opf_content)
    except:
        logger.error("Unable to parse opf xml")
        return result

    for main_element in root:
        logger.debug("looking at main element {}".format(main_element.tag))

        if not re.match(".*metadata$", main_element.tag):
            continue

        for metadata_tag in main_element:
            text = clean_string(metadata_tag.text)
            if text is None:
                continue
            
            if re.match(".*title$", metadata_tag.tag):
                result['title'] = text
            elif re.match(".*language$", metadata_tag.tag):
                result['principal_language'] = text
            elif re.match(".*creator$", metadata_tag.tag):
                result['author_names'].append(text)
            elif re.match(".*date$", metadata_tag.tag):
                def only_year(iso_date):
                    m = re.match("^[0-9]{4}", iso_date)
                    if m is None:
                        return None
                    else:
                        return m.group(0)

                publication_year = only_year(text)
                if publication_year is not None:
                    result['publication_year'] = publication_year
            else:
                logger.debug("Found unsupported tag {} => {}".format(metadata_tag.tag, text))

    return result


def get_metadata(instream):
    try:
        with zipfile.ZipFile(instream, 'r') as inzip:
            opf_path = _get_path_of_content_opf(inzip)
            opf_content = _read_content_opf(inzip, opf_path)

            result = get_metadata_from_opf_string(opf_content)
    except zipfile.BadZipfile:
        raise ValueError("Unable to open epub zip")
    instream.seek(0)
    return result


def is_responsible_for_extension(extension):
    return extension.lower() == 'epub'


if __name__ == "__main__":
    logging.basicConfig()

    ins = file("in.epub", "rb")
    outs = file("out.epub", "w+b")
    clear_metadata(ins, outs)
    # print get_metadata(ins)


# coding=utf-8
import mobi
import epub
import pdf

import os
import tempfile
import subprocess
import cStringIO

modules = (mobi, epub, pdf)


def responsible_module(extension):
    extension = extension.lower()
    for m in modules:
        if m.is_responsible_for_extension(extension):
            return m
    return None


def clear_metadata(source_stream, extension, output_stream):
    """ may raise a ValueError if the file could not be parsed ( ^= broken ) """
    m = responsible_module(extension)
    if m:
        result = m.clear_metadata(source_stream, output_stream)
        if result is None:
            raise AssertionError("Module did not adhere to add strip_file api")
        return result
    return False


def add_plain_metadata(source_stream, tome_file, output_stream, author_docs, tome_doc):
    """ may raise a ValueError if the file could not be parsed ( ^= broken ) """
    m = responsible_module(tome_file['file_extension'])
    if m:
        result = m.add_metadata(source_stream, output_stream, author_docs, tome_doc, tome_file)
        if result is None:
            raise AssertionError("Module did not adhere to add metadata api")
        return result
    return False


def extract_metadata(source_stream, extension):
    """ returns a dictionary that might contain the following fields:
        - tile
        - subtitle
        - edition
        - author_names[]
    """
    m = responsible_module(extension)
    if m:
        try:
            return m.get_metadata(source_stream)
        except ValueError:
            return {'author_names': []}
    return {'author_names': []}


# noinspection PyUnusedLocal
def extract_fulltext(source_stream):
    """ returns a fulltext representation of the file contents or None if none available
    """
    pass


def get_cover_image(source_stream, extension):
    """ returns a cStringIO stream with the contents of the cover file """
    # write into a temp file as to prevent ebook_convert from accessing the file store directly
    # and this way we can make sure that the file has the correct extension
    input_file_fd, input_file_path = tempfile.mkstemp(prefix = 'pydb_get_cover', suffix='.' + extension)
    input_file_in_tmp = os.fdopen(input_file_fd, 'wb')
    input_file_in_tmp.write(source_stream.read())
    input_file_in_tmp.close()

    fd_target, path_cover_target = tempfile.mkstemp(prefix = 'pydb_cover', suffix='.jpg')
    os.close(fd_target)

    subprocess.call(['ebook-meta', input_file_path, '--get-cover', path_cover_target])
    os.remove(input_file_path)

    if os.path.getsize(path_cover_target) == 0:
        os.remove(path_cover_target)
        return None

    with open(path_cover_target, 'rb') as coverfile:
        result = cStringIO.StringIO(coverfile.read())

    os.remove(path_cover_target)

    return result


if __name__ == '__main__':
    md = extract_metadata(file('in.epub', 'rb'), "ePuB")
    print repr(md)

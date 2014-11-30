import mobi
import epub
import pdf

modules = (mobi, epub, pdf)


def responsible_module(extension):
    extension = extension.lower()
    for m in modules:
        if m.is_responsible_for_extension(extension):
            return m
    return None


def strip_file(source_path, extension, output_stream):
    """ may raise a ValueError if the file could not be parsed ( ^= broken ) """
    m = responsible_module(extension)
    if m:
        result = m.clear_metadata(file(source_path, 'rb'), output_stream)
        if result is None:
            raise Exception("Module did not adhere to add strip_file api")
        return result
    return False


def add_plain_metadata(source_stream, tome_file, output_stream, author_docs, tome_doc):
    m = responsible_module(tome_file['file_extension'])
    if m:
        result = m.add_metadata(source_stream, output_stream, author_docs, tome_doc, tome_file)
        if result is None:
            raise Exception("Module did not adhere to add metadata api")
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


if __name__ == '__main__':
    md = extract_metadata(file('in.epub', 'rb'), "ePuB")
    print repr(md)
import sys
import optparse

import PyPDF2
import PyPDF2.utils
import logging

logger = logging.getLogger("ebook_metadata_tools.pdf")

def extract_fulltext(source_stream):
    pdf = PyPDF2.PdfFileReader(source_stream)
    content = ""

    for i in range(0, pdf.getNumPages()):
        extractedText = pdf.getPage(i).extractText()
        content += extractedText + "\n"

    content = " ".join(content.replace("\xa0", " ").strip().split())
    return content.encode("ascii", "ignore")


# noinspection PyUnusedLocal
def add_metadata(source_stream, output_stream, author_docs, tome_doc, tome_file):
    return False
    # this is currently broken due to problems using pypdf2 - e.g. destroying of bookmarks, non-idempotency of strip

    try:
        merger = PyPDF2.PdfFileMerger()
        merger.append(source_stream)

        author_names = [author_doc['name'] for author_doc in author_docs]
        metadata = {
            '/Author': ', '.join(author_names),
            '/Title': tome_doc['title']
        }

        if tome_doc['subtitle']:
            metadata['/Subtitle'] = tome_doc['subtitle']

        merger.addMetadata(metadata)
        merger.write(output_stream)
        return True
    except (PyPDF2.utils.PdfReadError, TypeError, AssertionError, IOError, RuntimeError) as e:
        logger.error("Caught an pypdf error: {}, skipping metadata add".format(e.message))
        return False



# noinspection PyUnusedLocal
def get_metadata(instream):
    result = {'author_names': []}

    try:
        pdf = PyPDF2.PdfFileReader(instream)
        doc_info = pdf.getDocumentInfo()
    except (PyPDF2.utils.PdfReadError, TypeError, AssertionError, IOError, RuntimeError) as e:
        logger.error("Caught an pypdf error: {}, skipping metadata read".format(e.message))
        return result

    if doc_info is None:
        return result

    for key, value in doc_info.iteritems():
        key = key.lower()
        value = unicode(value).strip()
        if not value:
            continue

        if key == "/author":
            result['author_names'].append(value)
        elif key == '/title':
            result['title'] = value
        elif key == '/subtitle':
            result['subtitle'] = value

    return result


# noinspection PyUnusedLocal
def clear_metadata(source_stream, output_stream):
    # this is currently broken due to problems using pypdf2 - e.g. destroying of bookmarks, non-idempotency of strip
    return False

    try:
        merger = PyPDF2.PdfFileMerger()
        merger.append(source_stream)
        merger.write(output_stream)
        return True
    except (PyPDF2.utils.PdfReadError, TypeError, AssertionError, IOError, RuntimeError) as e:
        logger.error("Caught an pypdf error: {}, skipping metadata erase".format(e.message))
        return False


def is_responsible_for_extension(extension):
    return extension.lower() == 'pdf'


if __name__ == "__main__":

    def main():
        usage = "usage: %prog [options] input_pdf_file"
        epilog = "example: pdf.py inputfile.pdf\n"
        parser = optparse.OptionParser(usage=usage, epilog=epilog)
        (options, args) = parser.parse_args()
        if len(args) != 1:
            parser.print_help()
            sys.exit(1)

        infile, = args

        print 'extracting...\n'
        infilestream = open(infile, "rb")


        # fulltext = extract_fulltext(infilestream)
        # print 'completed:\n'
        # print fulltext

        # metadata = get_metadata(infilestream)
        # print metadata

        # outs = file("out.pdf", "w+b")
        # clear_metadata(infilestream, outs)

        return 0

    sys.exit(main())

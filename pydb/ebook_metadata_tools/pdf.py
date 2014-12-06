import sys
import optparse


def extract_fulltext(source_stream):
    from PyPDF2.pdf import PdfFileReader
    pdf = PdfFileReader(source_stream)
    content = ""

    for i in range(0, pdf.getNumPages()):
        extractedText = pdf.getPage(i).extractText()
        content += extractedText + "\n"

    content = " ".join(content.replace("\xa0", " ").strip().split())
    return content.encode("ascii", "ignore")


# noinspection PyUnusedLocal
def add_metadata(source_stream, output_stream, author_docs, tome_doc, tome_file):
    return False


# noinspection PyUnusedLocal
def get_metadata(instream):
    return {'author_names': []}


# noinspection PyUnusedLocal
def clear_metadata(source_stream, output_stream):
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
        fulltext = extract_fulltext(infilestream)
        print 'completed:\n'
        print fulltext

        return 0

    sys.exit(main())
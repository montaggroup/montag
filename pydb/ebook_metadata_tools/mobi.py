#  0.1 - based on code from exthupd.py 0.26
# which is based on mobiunpack http://www.mobileread.com/forums/showthread.php?t=61986

import struct
import sys
import optparse
from pydb.title import coalesce_title


def _get_empty_extheader(extheader):
    new_items = 0

    l = 0
    tmp_hdr = extheader[0:4] + struct.pack('>L', l + 12) + struct.pack('>L', new_items)
    new_exthhdr = tmp_hdr

    # padding
    l = len(new_exthhdr)
    m = ((l // 4) + 1) * 4
    while l < m:
        new_exthhdr += struct.pack('>b', 0)
        l += 1

    return new_exthhdr


class Sectionizer:
    def __init__(self, stream):
        self.f = stream
        header = self.f.read(78)
        self.rawheader = header
        self.identifier = header[0x3C:0x3C + 8]
        self.num_sections, = struct.unpack_from('>L', header, 74)
        sections = self.f.read(self.num_sections * 8)
        self.rawsections = sections
        self.sections = struct.unpack_from('>%dL' % (self.num_sections * 2), sections, 0)[::2] + (0xfffffff, )
        self.indices = struct.unpack_from('>%dL' % (self.num_sections * 2), sections, 0)[1::2] + (0xfffffff, )

    def db_title(self):
        return self.rawheader[0:32]

    def set_db_title(self, db_title):
        a = db_title[0:32]
        a += "\0" * (32 - len(a))
        self.rawheader = a.encode('ascii', 'ignore') + self.rawheader[32:]

    def load_section(self, section):
        before, after = self.sections[section:section + 2]
        self.f.seek(before)
        return self.f.read(after - before)


def _write_new_header(outstream, sect, diff, new_exthhdr, new_mobihdr, palmdoc):
    outstream.write(sect.rawheader)
    before, after = sect.sections[0:2]
    index, = sect.indices[0:1]
    outstream.write(struct.pack('>L', before))
    outstream.write(struct.pack('>L', index))
    for i in xrange(1, sect.num_sections):
        before, after = sect.sections[i:i + 2]
        index, = sect.indices[i:i + 1]
        outstream.write(struct.pack('>L', before + diff))
        outstream.write(struct.pack('>L', index))
    outstream.write(struct.pack('>h', 0))
    outstream.write(palmdoc)
    outstream.write(new_mobihdr)
    outstream.write(new_exthhdr)
    for i in xrange(1, sect.num_sections):
        data = sect.load_section(i)
        outstream.write(data)


def _extract_title(header):
    title_offset, title_len = struct.unpack('>II', header[0x54:0x5c])
    title_end = title_offset + title_len
    title = header[title_offset:title_end]
    return title, title_len


def _parse_headers(sect):
    # get header ( section_0)
    header = sect.load_section(0)
    # get palmdoc header
    palmdoc = header[0:16]
    # get MOBI header
    mobi_header_length, _type, codepage, unique_id, version = struct.unpack('>LLLLL', header[20:40])
    mobihdr = header[16:16 + mobi_header_length]
    mobi_id = mobihdr[0:4]
    if mobi_id != 'MOBI':
        raise ValueError('MOBI identifier not found')
    # if exth region exists then parse it for the metadata
    exth_flag, = struct.unpack('>L', header[0x80:0x84])
    if exth_flag & 0x40:
        # get EXTH header
        exth_id = header[16 + mobi_header_length:16 + mobi_header_length + 4]

        if exth_id != 'EXTH':
            raise ValueError('EXTH identifier not found')
    new_exthhdr = _get_empty_extheader(header[16 + mobi_header_length:])
    return header, mobi_header_length, mobihdr, new_exthhdr, palmdoc


def clear_metadata(instream, outstream, new_title=""):
    new_title = new_title.encode('ascii', 'ignore')
    new_title_len = len(new_title)

    sect = Sectionizer(instream)
    if sect.identifier != 'BOOKMOBI' and sect.identifier != 'TEXtREAd':
        raise ValueError('invalid file format')

    header, mobi_header_length, mobihdr, new_exthhdr, palmdoc = _parse_headers(sect)
    # add new_title to new_exthhdr
    new_exthlen = len(new_exthhdr)
    # print mobi_header_length

    sect.set_db_title(new_title)

    # padding
    l = new_exthlen+new_title_len
    m = ((l // 4) + 1) * 4
    while l < m:
        new_title += struct.pack('>b', 0)
        l += 1

    # write title offset and title length, title to be placed after ext header
    new_mobihdr = mobihdr[0:68]
    new_mobihdr += struct.pack('>L', 16 + mobi_header_length + new_exthlen)
    new_mobihdr += struct.pack('>L', new_title_len)
    new_mobihdr += mobihdr[76:]

    old_len = len(header)
    new_len = 16 + mobi_header_length + l
    diff = new_len - old_len

    _write_new_header(outstream, sect, diff, new_exthhdr+new_title, new_mobihdr, palmdoc)
    return True


def clear_metadata_from_file(infile, outfile, new_title=""):
    instream = file(infile, 'rb')
    outstream = file(outfile, 'wb')
    clear_metadata(instream, outstream, new_title)

    instream.close()
    outstream.close()


def add_metadata(source_stream, output_stream, author_docs, tome_doc, tome_file):
    author_names = {author_doc['name'] for author_doc in author_docs}
    tome_title = coalesce_title(tome_doc['title'], tome_doc['subtitle'])

    file_title =  u"{} - {} ({})".format(','.join(author_names), tome_title, tome_file['hash'])
    clear_metadata(source_stream, output_stream, new_title=file_title)
    return True


def get_metadata(instream):
    sect = Sectionizer(instream)
    if sect.identifier != 'BOOKMOBI' and sect.identifier != 'TEXtREAd':
        raise ValueError('invalid file format')

    header, mobihdr_length, mobihdr, new_exthhdr, palmdoc = _parse_headers(sect)

    # get book title
    title, _ = _extract_title(header)
    result = {'author_names': [], 'title': title}
    instream.seek(0)
    return result


def is_responsible_for_extension(extension):
    return extension.lower() in ('mobi', 'azw')


if __name__ == "__main__":

    def main():
        usage = "usage: %prog [options] input_mobi_file output_mobi_file"
        epilog = "example: exthclean.py inputfile.mobi\n"
        parser = optparse.OptionParser(usage=usage, epilog=epilog)
        (options, args) = parser.parse_args()
        if len(args) != 2:
            parser.print_help()
            sys.exit(1)

        infile, outfile, = args

        try:
            clear_metadata_from_file(infile, outfile, "some_short_title")

        except ValueError, e:
            print "error: %s" % e
            return 1

        return 0

    clear_metadata_from_file('in.mobi', 'out.mobi', "This is title")
#    sha256sum = hashlib.sha256(open('in.mobi', 'rb').read()).hexdigest()
#    print "sha256(in)={}".format(sha256sum)
#    sha256sum = hashlib.sha256(open('out.mobi', 'rb').read()).hexdigest()
#    print "sha256(out)={}".format(sha256sum)

    #print get_metadata(file('in.mobi', 'rb'))
#    sys.exit(main())

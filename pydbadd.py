#!/usr/bin/env python2.7

import Pyro4
import argparse
import os
import sys
from pydb import FileType, TomeType

import pydb.opf

sys.excepthook = Pyro4.util.excepthook

parser = argparse.ArgumentParser(description='Adds a tome to the database.')
# parser.add_argument('--ignore-opf','-i', help='Ignore any metadata.opf file found in the same directory', action=store_true, default=False)
parser.add_argument('--non-fiction', '-n', dest='tome_type', help='Sets the tome type to non-ficton',
                    action='store_const', const='nonfiction')
parser.add_argument('--fiction', '-f', dest='tome_type', help='Sets the tome-type to fiction', action='store_const',
                    const='fiction')
parser.add_argument('--fidelity',
                    help='The fidelity value of all components that will be added, ranging from -100 to 100', type=int,
                    default='50')
parser.add_argument('--delete', '-d', help="Delete source file after successful import", action="store_true",
                    default=False)

parser.add_argument('filepaths', nargs='+')

args = parser.parse_args()

import pydb.pyrosetup

db = pydb.pyrosetup.pydbserver()

if db.ping() != "pong":
    print >> sys.stderr, "Unable to talk to server, is it running?`"
    sys.exit(-1)


def read_metadata(filepath):
    base, extension = os.path.splitext(filepath)
    metadata_path = base + '.opf'
    if not os.path.exists(metadata_path):
        dir, file = os.path.split(filepath)
        metadata_path = os.path.join(dir, 'metadata.opf')
        if not os.path.exists(metadata_path):
            raise Exception('No metadata file found')

    return pydb.opf.Metadata.from_file(metadata_path)


def title_split(title):
    subtitle = None
    title = title.strip()
    if ":" in title:
        title, subtitle = title.split(':', 1)
        title = title.strip()
        subtitle = subtitle.strip()
    return title, subtitle


def add_file(filepath, fidelity, tome_type, delete_source):
    print "Adding", repr(filepath)
    filepath = os.path.abspath(filepath)
    metadata = read_metadata(filepath)

    author_ids = db.find_or_create_authors(metadata.authors, fidelity=fidelity)

    title, subtitle = title_split(metadata.title)
    # print 'tome cands: ',tome_candidates
    print "Metadata tags: {}".format(metadata.tags)
    tome_id = db.find_or_create_tome(title, metadata.language, author_ids, subtitle, tome_type=tome_type,
                                     fidelity=fidelity, tags_values=metadata.tags, publication_year=metadata.publication_year)


    # \todo the file might already be linked to another tome, that ain't generic or completely different - we should handle that  
    base, extension = os.path.splitext(filepath)
    extension = extension[1:]  # remove period

    (file_id, file_hash, size) = pydb.pyrosetup.fileserver().add_file_from_local_disk(filepath, extension,
                                                                                      move_file=delete_source)
    if file_id:
        db.link_tome_to_file(tome_id, file_hash, size, file_extension=extension, file_type=FileType.Content,
                             fidelity=fidelity)
    else:
        print u"Unable to add file '{}' to db - check whether it might be defective".format(filepath)


tome_type = TomeType.Unknown
if args.tome_type == 'nonfiction':
    tome_type = TomeType.NonFiction
elif args.tome_type == 'fiction':
    tome_type = TomeType.Fiction
else:
    assert not args.tome_type, 'Invalid tome type selected: ' + str(tome_type)

for filepath in args.filepaths:
    filepath = unicode(filepath.decode(sys.stdin.encoding))  # decode stuff coming in from command line

    add_file(filepath, args.fidelity, tome_type, args.delete)
    



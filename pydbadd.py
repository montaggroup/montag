#!/usr/bin/env python2.7
# coding=utf-8

import Pyro4
import argparse
import os
import sys

from pydb import FileType, TomeType
import pydb.title
import pydb.opf


def read_metadata(filepath):
    base, extension = os.path.splitext(filepath)
    metadata_path = base + '.opf'
    if not os.path.exists(metadata_path):
        dir_name, file_name = os.path.split(filepath)
        metadata_path = os.path.join(dir_name, 'metadata.opf')
        if not os.path.exists(metadata_path):
            raise Exception('No metadata file found')

    return pydb.opf.read_metadata_from_file(metadata_path)


def add_file(db, file_server, filepath, fidelity, tome_type, delete_source):
    print u"Adding {}".format(filepath)
    filepath = os.path.abspath(filepath)
    metadata = read_metadata(filepath)

    author_ids = db.find_or_create_authors(metadata.authors, fidelity=fidelity)

    title, subtitle, edition = pydb.title.title_split(metadata.title)

    if metadata.edition is not None:
        edition = metadata.edition

    print u'Metadata tags: {}'.format(metadata.tags)
    tome_id = db.find_or_create_tome(title, metadata.language, author_ids,
                                     subtitle, tome_type=tome_type,
                                     fidelity=fidelity, edition=edition,
                                     publication_year=metadata.publication_year,
                                     tags_values=metadata.tags)

    # \todo the file might already be linked to another tome, that ain't generic or completely different
    # we should handle that
    base, extension = os.path.splitext(filepath)
    extension = extension[1:]  # remove period

    (file_id, file_hash, size) = file_server.add_file_from_local_disk(filepath, extension,
                                                                                      move_file=delete_source)
    if file_id:
        db.link_tome_to_file(tome_id, file_hash, size, file_extension=extension, file_type=FileType.Content,
                             fidelity=fidelity)
    else:
        print u"Unable to add file '{}' to db - check whether it might be defective".format(filepath)


def add_file_only(file_server, filepath, delete_source):
    filepath = os.path.abspath(filepath)
    base, extension = os.path.splitext(filepath)
    extension = extension[1:]  # remove period
    file_server.add_file_from_local_disk(filepath, extension, move_file=delete_source)


def main():
    sys.excepthook = Pyro4.util.excepthook

    parser = argparse.ArgumentParser(description='Adds a tome to the database.')
    parser.add_argument('--non-fiction', '-n', dest='tome_type', help='Sets the tome type to non-ficton',
                        action='store_const', const='nonfiction')
    parser.add_argument('--fiction', '-f', dest='tome_type', help='Sets the tome-type to fiction', action='store_const',
                        const='fiction')
    parser.add_argument('--fidelity',
                        help='The fidelity value of all components that will be added, ranging from -100 to 100',
                        type=int, default='50')
    parser.add_argument('--delete', '-d', help="Delete source file after successful import", action="store_true",
                        default=False)
    parser.add_argument('--add-file-only', action="store_true", default=False,
                        help="Do not read metadata and do not create a new tome, just put the file into the filestore.")
    parser.add_argument('--only-if-file-known', action="store_true", default=False,
                        help="Option for --add-file-only: Do only add the file if is known to the database")
    parser.add_argument('--verbose', '-v', action="store_true", default=False,
                        help="Be more verbose")

    parser.add_argument('filepaths', nargs='+')

    args = parser.parse_args()

    import pydb.pyrosetup

    db = pydb.pyrosetup.pydbserver()

    if db.ping() != "pong":
        print >> sys.stderr, "Unable to talk to server, is it running?`"
        sys.exit(-1)

    file_server = pydb.pyrosetup.fileserver()

    tome_type = TomeType.Unknown
    if args.tome_type == 'nonfiction':
        tome_type = TomeType.NonFiction
    elif args.tome_type == 'fiction':
        tome_type = TomeType.Fiction
    else:
        assert not args.tome_type, 'Invalid tome type selected: ' + str(tome_type)

    for filepath in args.filepaths:
        filepath = unicode(filepath.decode(sys.stdin.encoding))  # decode stuff coming in from command line

        if args.add_file_only:
            if args.only_if_file_known:
                abspath = os.path.abspath(filepath)
                base, extension = os.path.splitext(filepath)
                extension = extension[1:]  # remove period
                if not file_server.is_file_known(abspath, extension):
                    if args.verbose:
                        print >> sys.stderr, u"File {} not known to database, skipping".format(filepath)
                        continue

            if args.verbose:
                print >> sys.stderr, u"Adding file {}".format(filepath)
            add_file_only(file_server, filepath, args.delete)
        else:
            if args.verbose:
                print >> sys.stderr, u"Adding file with tome {}".format(filepath)
            add_file(db, file_server, filepath, args.fidelity, tome_type, args.delete)


if __name__ == "__main__":
    main()




#!/usr/bin/env python2.7
# coding=utf-8

import Pyro4
import argparse
import sys
import logging
import os

from pydb import importer
from pydb import identifier_runner
from pydb import executionenvironment
from pydb import importerdb

logger = logging.getLogger('pydbbulkimport')


def list_all_files(folder_path):
    result = []

    logger.debug('Checking {}'.format(folder_path))
    for dirname, dir_names, filenames in os.walk(folder_path):
        for filename in filenames:
            full_path = os.path.join(dirname, filename)
            result.append(full_path)
    logger.debug('Found files: {}'.format(result))
    return result


def clear_empty_folders(folder_path):
    deleted_one = True
    while deleted_one:
        deleted_one = False
        for dirname, dirnames, filenames in (os.walk(folder_path)):
            for subdirname in dirnames:
                dir_path = os.path.join(dirname, subdirname)
                try:
                    os.rmdir(dir_path)
                    logger.debug('Deleted empty folder: {}'.format(dir_path))
                    deleted_one = True
                except OSError:
                    pass  # we only want to delete empty folders


def main():
    sys.excepthook = Pyro4.util.excepthook

    parser = argparse.ArgumentParser(description='Adds a folder of tomes to the database.')
    parser.add_argument('--delete', '-d', dest='delete', action='store_true', default=False,
                        help='Deletes all files after processing')
    parser.add_argument('--group_name', '-g',
                        help='A name to be stored as the name of the import group, e.g. "books_from_school 2017"',
                        type=unicode)
    parser.add_argument('--verbose', '-v', action="store_true", default=False,
                        help="Be more verbose")
    parser.add_argument('--basepath', '-b', dest='basepath', help='Sets the basepath for the server', action='store')
    parser.add_argument('folderpaths', nargs='+')

    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    db_dir = executionenvironment.determine_database_directory(args.basepath)
    schema_dir = executionenvironment.get_schema_dir()

    import pydb.pyrosetup

    db = pydb.pyrosetup.pydbserver()

    if db.ping() != "pong":
        print >> sys.stderr, "Unable to talk to server, is it running?`"
        sys.exit(-1)

    file_server = pydb.pyrosetup.fileserver()

    importer_db_path = importer.db_path(db_dir, 'importer')
    importer_db = importerdb.ImporterDB(importer_db_path, schema_dir)

    for path in args.folderpaths:
        local_importer = importer.Importer(file_server, importer_db, path, None, args.group_name, args.delete)
        files = list_all_files(path)
        local_importer.new_files_found(files)
        if args.delete:
            clear_empty_folders(path)

    identifier_runner_ = identifier_runner.build_identifier_runner(db_dir, schema_dir, importer_db=importer_db)
    identifier_runner_.run_on_all_unprocessed_files()


if __name__ == "__main__":
    main()


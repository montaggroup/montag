#!/usr/bin/env python

# coding=utf-8
import argparse
import sys
import importlib

from pydb import identifier_runner
from pydb import executionenvironment
from pydb import pyrosetup
from pydb import importerdb
from pydb import importer

import logging

def main():
    parser = argparse.ArgumentParser(
        description='Runs a specified file identifier.')
    parser.add_argument('identifier_name')
    parser.add_argument('filter_string', default='', nargs='?',
                        help='Filter String: Either emtpy => all or group_name=GROUP_NAME')

    parser.add_argument('--basepath', '-b', dest='basepath', help='Sets the basepath for the server', action='store')
    parser.add_argument('--verbose', '-v', action="store_true", default=False,
                        help="Be more verbose")

    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    group_filter = build_group_filter(args.filter_string)

    pydb_ = pyrosetup.pydbserver()
    file_server = pyrosetup.fileserver()

    db_dir = executionenvironment.determine_database_directory(args.basepath)
    schema_dir = executionenvironment.get_schema_dir()

    run(pydb_, file_server, db_dir, schema_dir, args.identifier_name, group_filter)


def build_group_filter(filter_string):
    if filter_string:
        try:
            key, value = filter_string.split('=')
            if key != 'group_name':
                raise ValueError('Only group_name is supported at the moment')
            return value

        except (ValueError, KeyError) as e:
            print "Unable to parse filter string: {}".format(e.message)
            sys.exit(-2)


def run(pydb_, file_server, db_dir, schema_dir, identifier_name, group_filter):
    importer_db_path = importer.db_path(db_dir, 'importer')
    importer_db = importerdb.ImporterDB(importer_db_path, schema_dir=schema_dir)

    identifier_module = importlib.import_module('pydb.identifiers.' + identifier_name)
    identifier = identifier_module.build(pydb_, file_server)

    runner = identifier_runner.IdentifierRunner(pydb_, file_server, [identifier], importer_db)

    runner.run_on_pending_files(group_filter)


if __name__ == '__main__':
    main()

#!/usr/bin/env python2.7

import argparse
import logging
import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))

import pydb.pyrosetup

logger = logging.getLogger("rakf")

file_server = pydb.pyrosetup.fileserver()


def already_known_book(filepath):
    base, extension = os.path.splitext(filepath)
    extension = extension[1:]  # remove dot

    abspath = os.path.abspath(filepath)
    try:
        return file_server.is_file_known(abspath, extension)
    except ValueError:
        print "Ex"
        return False


def remove_already_known_ebooks(path, dry_run=False):
    check_count = 0
    remove_count = 0

    def log_progress():
        logger.info("%d/%d removed %0.1f %%" % (remove_count, check_count, remove_count * 100.0 / check_count))

    for dir_name, dirs, files in os.walk(path):
        for f in files:
            _, f_ext = os.path.splitext(f)
            if f_ext.lower() == '.opf':
                continue

            file_path = os.path.join(dir_name, f)
            logger.debug("Checking {}".format(file_path))
            check_count += 1

            if already_known_book(file_path):
                if dry_run:
                    logger.info("Would remove {}".format(file_path))
                else:
                    logger.info("Removing {}".format(file_path))
                    os.remove(file_path)

                remove_count += 1

            if check_count % 10 == 0:
                log_progress()

    if check_count > 0 and check_count % 10 != 0:
        log_progress()


def main():
    parser = argparse.ArgumentParser(description='Removes files that are already known to the database')
    parser.add_argument('paths', help='Path to file or directory to scan', nargs='+')
    parser.add_argument('-d', '--debug', help='Enables debug output', action='store_true')
    parser.add_argument('-n', '--dry-run', help='Do not really delete files', action='store_true')

    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO, format="%(name)8s: %(message)s")

    for path in args.paths:
        remove_already_known_ebooks(path, args.dry_run)

if __name__ == "__main__":
    main()



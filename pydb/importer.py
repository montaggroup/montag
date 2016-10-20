# coding=utf-8

import os
import time
import stat
import logging
import hashlib
import json

import importerdb
import ebook_metadata_tools

DELETE_EMPTY_SECONDS_DELAY = 300
DEFAULT_POLL_INTERVAL = 3

logger = logging.getLogger(__name__)

SUPPORTED_IMPORTER_FILE_EXTENSIONS = ['epub', 'mobi', 'pdf', 'lit', 'djvu', 'azw3', 'azw4', 'cbr']


def db_path(db_dir, db_name):
    return os.path.join(db_dir, db_name + ".db")


def build_importer(file_server, db_dir, schema_dir, watch_folder_path, notification_queue):
    importer_db_path = db_path(db_dir, 'importer')
    db = importerdb.ImporterDB(importer_db_path, schema_dir)
    importer = Importer(file_server, db, watch_folder_path, notification_queue)
    return importer


def build_watcher(importer, watch_folder_path, reactor):
    watcher = DirectoryWatcher(watch_folder_path, importer.new_files_found, DEFAULT_POLL_INTERVAL, reactor)
    return watcher


class Importer(object):
    def __init__(self, fileserver, importerDB, import_folder_path, notification_queue):
        """
        :type importerDB: importerdb.ImporterDB
        """
        self.fileserver = fileserver
        self.db = importerDB
        self.import_folder_path = import_folder_path
        self.notification_queue = notification_queue

    def new_files_found(self, full_path_list):
        for f in full_path_list:
            logger.debug('Will import {}'.format(f))
            try:
                self.import_file(f)
                logger.info('Imported {}'.format(f))
                self.notification_queue.put(True)
            except Exception as e:
                logger.error('Unable to import file {}: {}'.format(f, e.message))
            delete_file(f)

    def import_file(self, file_path):
        _, ext_with_dot = os.path.splitext(file_path)
        ext = ext_with_dot[1:].lower()
        if ext not in SUPPORTED_IMPORTER_FILE_EXTENSIONS:
            raise ValueError('{}: Unsupported file extension'.format(file_path))

        metadata = {}
        with open(file_path, 'rb') as file_stream:
            try:
                metadata = ebook_metadata_tools.extract_metadata(file_stream, ext)
            except Exception as e:
                logger.warning('Unable to parse metadata from {}: {}', file_path, e.message)

        md5sum = md5sum_file(file_path)

        local_file_id, file_hash, size = self.fileserver.add_file_from_local_disk(file_path, ext, move_file=True)

        if self.db.is_file_known(file_hash):
            raise ValueError('File {} already known'.format(file_hash))

        self.db.begin()
        self.db.add_file(file_hash)
        self.db.add_fact(file_hash, 'md5', md5sum)
        self.db.add_fact(file_hash, 'file_extension', ext)
        self.db.add_fact(file_hash, 'file_size', size)

        relative_file_path = file_path.replace(self.import_folder_path, "")
        logger.debug('Relative path of {}: {}'.format(file_path, relative_file_path))
        self.db.add_fact(file_hash, 'path', relative_file_path)

        _, file_name = os.path.split(file_path)
        self.db.add_fact(file_hash, 'file_name', file_name)

        self.db.add_fact(file_hash, 'file_metadata', json.dumps(metadata))
        self.db.commit()


class DirectoryWatcher(object):
    def __init__(self, folder_path, new_files_func, poll_interval, reactor):
        self.folder_path = folder_path
        self.new_files_func = new_files_func
        self.poll_interval = poll_interval
        self.reactor = reactor
        if not os.path.exists(folder_path):
            raise IOError('Watch folder "{}" does not exist!'.format(folder_path))

    def start(self):
        logger.debug('Watcher started')
        self._check_folder()

    def _check_folder(self):
        self.reactor.callLater(self.poll_interval, self._check_folder)
        all_files = self._list_all_files()
        self.new_files_func(all_files)

    def _list_all_files(self):
        result = []

        logger.debug('Checking {}'.format(self.folder_path))
        for dirname, dirnames, filenames in os.walk(self.folder_path):
            for subdirname in dirnames:
                dir_path = os.path.join(dirname, subdirname)
                # @todo: can we make this more elegant?
                if file_age(dir_path) > DELETE_EMPTY_SECONDS_DELAY:  # we want to remove empty folders to reduce clutter
                    try:
                        os.rmdir(dir_path)
                    except OSError:
                        pass  # we only want to delete empty folders

            for filename in filenames:
                if filename != 'README':
                    full_path = os.path.join(dirname, filename)
                    result.append(full_path)

        logger.debug('Found files: {}'.format(result))
        return result


def file_age(pathname):
    return time.time() - os.stat(pathname)[stat.ST_MTIME]


def delete_file(file_path):
    if not os.path.exists(file_path):
        return

    try:
        os.unlink(file_path)
    except Exception as e:
        logger.error('Could not delete {}: {}'.format(file_path, e.message))


def md5sum_file(path):
    return md5_stream(open(path, 'rb'))


def md5_stream(stream):
    chunk_size_bytes = 100*1000

    hash_algo = hashlib.md5()
    buf = stream.read(chunk_size_bytes)
    while buf:
        hash_algo.update(buf)
        buf = stream.read(chunk_size_bytes)
    return hash_algo.hexdigest()
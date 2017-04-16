# coding=utf-8

import os
import time
import stat
import logging
import hashlib
import json

import sqlitedb
import importerdb
import ebook_metadata_tools

DELETE_EMPTY_FOLDERS_DELAY = 300  # empty folders will be deleted if they are older than this
DEFAULT_POLL_INTERVAL = 5  # check import watch every x seconds
MIN_FILE_STABLE_PERIOD = 30  # if file size remains stable for this number of seconds, begin import

logger = logging.getLogger(__name__)

SUPPORTED_IMPORTER_FILE_EXTENSIONS = ['epub', 'mobi', 'pdf', 'lit', 'djvu', 'azw3', 'azw4', 'cbr']


class FileRefusedError(Exception):
    pass


def db_path(db_dir, db_name):
    return os.path.join(db_dir, db_name + ".db")


def build_importer(file_server, db_dir, schema_dir, watch_folder_path, notification_queue, group_name, delete_after_import):
    importer_db_path = db_path(db_dir, 'importer')
    db = importerdb.ImporterDB(importer_db_path, schema_dir)
    importer = Importer(file_server, db, watch_folder_path, notification_queue, group_name, delete_after_import)
    return importer


def build_watcher(importer, watch_folder_path, reactor):
    watcher = DirectoryWatcher(watch_folder_path, importer.new_files_found, DEFAULT_POLL_INTERVAL, reactor)
    return watcher


class Importer(object):
    def __init__(self, fileserver, importer_db, import_folder_path, notification_queue, group_name, delete_after_import):
        """
        :type importer_db: importerdb.ImporterDB
        group_name: Optional group name which will be added as fact, default: None
        """
        self.fileserver = fileserver
        self.db = importer_db
        self.import_folder_path = import_folder_path
        self.notification_queue = notification_queue
        self.group_name = group_name
        self.delete_after_import = delete_after_import

    def new_files_found(self, full_path_list):
        for f in full_path_list:
            logger.debug('Will import {}'.format(f))
            try:
                self.import_file(f, self.delete_after_import)
                logger.info('Imported {}'.format(f))
                if self.notification_queue:
                    self.notification_queue.put(True)
                if self.delete_after_import:
                    delete_file(f)
            except FileRefusedError as e:
                logger.info('File {} refused by import: {}'.format(f, e.message))
                if self.delete_after_import:
                    delete_file(f)
            except Exception as e:
                logger.error('Unable to import file {}: {}'.format(f, e.message))

    def import_file(self, file_path, delete_after_import):
        _, ext_with_dot = os.path.splitext(file_path)
        ext = ext_with_dot[1:].lower()
        if ext not in SUPPORTED_IMPORTER_FILE_EXTENSIONS:
            raise FileRefusedError('Unsupported file extension')

        metadata = {}
        with open(file_path, 'rb') as file_stream:
            try:
                metadata = ebook_metadata_tools.extract_metadata(file_stream, ext)
            except Exception as e:
                logger.warning('Unable to parse metadata from {}: {}', file_path, e.message)

        md5sum = md5sum_file(file_path)

        local_file_id, file_hash, size = self.fileserver.add_file_from_local_disk(file_path, ext, move_file=delete_after_import)

        if self.db.is_file_known(file_hash):
            raise FileRefusedError('File already known to importer')

        with sqlitedb.Transaction(self.db):
            self.db.add_file(file_hash)
            self.db.add_fact(file_hash, 'md5', md5sum)
            self.db.add_fact(file_hash, 'file_extension', ext)
            self.db.add_fact(file_hash, 'file_size', size)
            if self.group_name:
                self.db.add_fact(file_hash, 'group_name', self.group_name)

            relative_file_path = file_path.replace(self.import_folder_path, '')
            logger.debug('Relative path of {}: {}'.format(file_path, relative_file_path))
            self.db.add_fact(file_hash, 'path', relative_file_path)

            _, file_name = os.path.split(file_path)
            self.db.add_fact(file_hash, 'file_name', file_name)

            self.db.add_fact(file_hash, 'file_metadata', json.dumps(metadata))


class FileStateChecker(object):
    def __init__(self, file_path):
        self.file_path = file_path

        self.last_change_timestamp = time.time()
        self.last_check_timestamp = self.last_change_timestamp
        self.last_known_size = 0

    def update(self):
        self.last_check_timestamp = time.time()

        size = os.path.getsize(self.file_path)
        if size != self.last_known_size:
            self.last_known_size = size
            self.last_change_timestamp = self.last_check_timestamp

    def is_file_stable(self):
        if self.last_check_timestamp - self.last_change_timestamp > MIN_FILE_STABLE_PERIOD:
            return True
        return False


class DirectoryWatcher(object):
    def __init__(self, folder_path, new_files_func, poll_interval, reactor):
        self.folder_path = folder_path
        self.new_files_func = new_files_func
        self.poll_interval = poll_interval
        self.reactor = reactor
        self.file_change_checks = {}
        if not os.path.exists(folder_path):
            raise IOError('Watch folder "{}" does not exist!'.format(folder_path))

    def start(self):
        logger.debug('Watcher started')
        self._check_folder()

    def _check_folder(self):
        self.reactor.callLater(self.poll_interval, self._check_folder)
        all_files = self._list_all_files()

        processable_files = []

        for file_path in all_files:
            if file_path not in self.file_change_checks:
                logger.debug('Starting to watch %s', file_path)
                self.file_change_checks[file_path] = FileStateChecker(file_path)
            checker = self.file_change_checks[file_path]
            checker.update()
            logger.debug('Checking %s', file_path)
            if checker.is_file_stable():
                logger.debug('File %s ready for import', file_path)
                processable_files.append(file_path)
                del(self.file_change_checks[file_path])

        if processable_files:
            self.new_files_func(processable_files)

    def _list_all_files(self):
        result = []

        logger.debug('Checking {}'.format(self.folder_path))
        for dirname, dirnames, filenames in os.walk(self.folder_path):
            for subdirname in dirnames:
                dir_path = os.path.join(dirname, subdirname)
                if file_age(dir_path) > DELETE_EMPTY_FOLDERS_DELAY:  # we want to remove empty folders to reduce clutter
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
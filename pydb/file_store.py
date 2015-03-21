import logging
import os
import shutil
import hashlib
import ebook_metadata_tools
import tempfile

logger = logging.getLogger('file_store')

import disk_usage
from pydb import assert_hash


class FileStore():
    def __init__(self, store_dir):
        self.store_dir = store_dir

    def disk_usage(self):
        total, used, free = disk_usage.disk_usage(self.store_dir)
        return total, used, free

    def get_local_file_path(self, file_hash, file_ext):
        cache_path = self._calculate_cache_path(file_hash) + '.' + file_ext
        return os.path.abspath(cache_path)

    def file_exists(self, file_hash, file_ext):
        return os.path.exists(self.get_local_file_path(file_hash, file_ext))

    def add_file(self, source_path, file_hash, extension, move_file):
        size = os.path.getsize(source_path)
        if size == 0:
            raise ValueError("File to add is zero bytes large")

        logger.debug(u"Hash is " + file_hash)

        cache_path = self._calculate_cache_path(file_hash) + '.' + extension
        logger.debug(u"Cache path is " + cache_path)

        if move_file:
            if not os.path.exists(cache_path):
                logger.debug(u"move from {} to {} .".format(source_path, cache_path))
                try:
                    shutil.move(source_path, cache_path)
                except:
                    logger.debug("move had issues, continuing for now")
            else:
                old_hash = hash_file(cache_path)
                if old_hash != file_hash:
                    logger.info(u"Old hash in file_store {} doesn't match the actual hash {} overwriting."
                                .format(old_hash, file_hash))
                    os.remove(cache_path)
                    shutil.move(source_path, cache_path)
        else:
            if not os.path.exists(cache_path):
                logger.debug(u"copy from {} to {} .".format(source_path, cache_path))
                shutil.copyfile(source_path, cache_path)
            else:
                old_hash = hash_file(cache_path)
                if old_hash != file_hash:
                    logger.info(u"Old hash in file_store {} doesn't match the actual hash {} overwriting."
                                .format(old_hash, file_hash))
                    shutil.copyfile(source_path, cache_path)

        if size != os.path.getsize(cache_path):
            raise ValueError(u"File sizes after insert do not match: {} bytes in file to insert, "
                            "{} bytes in store. Cache path is {}".format(size, os.path.getsize(cache_path), cache_path))

        if move_file and os.path.exists(source_path):
            os.remove(source_path)

        return size

    def _calculate_cache_path(self, file_hash):
        assert file_hash, "Hash must not be none"
        file_hash = file_hash.lower()
        assert_hash(file_hash)
        d1 = file_hash[0:2]
        d2 = file_hash[2:4]

        dir_name = os.path.join(self.store_dir, d1, d2)
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
        return os.path.join(dir_name, file_hash)


def hash_file(path):
    return hash_stream(open(path, 'rb'))


def hash_stream(stream):
    chunk_size_bytes = 100*1000

    hash_algo = hashlib.sha256()
    buf = stream.read(chunk_size_bytes)
    while buf:
        hash_algo.update(buf)
        buf = stream.read(chunk_size_bytes)
    return hash_algo.hexdigest()

def strip_file(source_stream, extension_without_dot, target_stream):
    """ returns true if stripped successfully,
        false if stripping not possible or not leading to a changed file
        and raises an exception if the source file is broken
    """
    return ebook_metadata_tools.clear_metadata(source_stream, extension_without_dot, target_stream)

def strip_file_to_temp(source_path, extension_without_dot, remove_original=False):
    """ returns the name of the new file and the new hash if stripped,
        None, None if stripping not possible or not leading to a new file
        and raises an exception if the source file is broken
    """
    (handle_stripped, filename_stripped) = tempfile.mkstemp(suffix='.' + extension_without_dot)
    logger.info(u"Writing to file {}".format(filename_stripped))

    success = False
    with os.fdopen(handle_stripped, "wb") as target_stream:
        with open(source_path, 'rb') as source_stream:
            if strip_file(source_stream, extension_without_dot, target_stream):
                success = True

    if success:
        if remove_original:
            os.remove(source_path)
        file_hash_after_stripping = hash_file(filename_stripped)
        return filename_stripped, file_hash_after_stripping
    else:
        os.remove(filename_stripped)
        return None, None

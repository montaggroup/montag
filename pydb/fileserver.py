import os
import logging
import file_store
import cStringIO

logger = logging.getLogger('fileserver')


def db_path(db_dir, db_name):
    return os.path.join(db_dir, db_name + ".db")


def build(file_store_path, pydb_server):
    file_store_ = file_store.FileStore(file_store_path)
    fs = FileServer(pydb_server, file_store_)
    return fs


class FileServer:
    def __init__(self, db, file_store_):
        self.db = db
        self.file_store = file_store_

    # noinspection PyMethodMayBeStatic
    def ping(self):
        """ returns a simple string to test whether the connection is working and the server is running """
        return "pong"

    def file_store_disk_usage(self):
        return self.file_store.disk_usage()

    def get_local_file_path(self, file_hash):
        """ returns a string containing the path to the file identified by hash or None """
        file_ext = self.db.get_file_extension(file_hash)
        if file_ext is not None:
            return self.file_store.get_local_file_path(file_hash, file_ext)

    def get_local_file_size(self, file_hash):
        """ returns a the file size of the file identified by hash if it's available locally. """
        path = self.get_local_file_path(file_hash)
        if path:
            return os.path.getsize(path)

    def is_file_known(self, source_path, extension_without_dot):
        """ returns true if the file specified by source_path is already attached to at least one tome
            raises an ValueError if the file is broken
        """
        effective_hash = _calculate_effective_hash(source_path, extension_without_dot)

        used_links = self.db.get_tome_files_by_hash(effective_hash)
        return bool(used_links)

    def is_file_in_store(self, source_path, extension_without_dot):
        """ returns true if the file specified by source path is already in the file store """
        effective_hash = _calculate_effective_hash(source_path, extension_without_dot)
        return self.file_store.file_exists(effective_hash, extension_without_dot)

    def add_file_from_local_disk(self, source_path, extension, only_allowed_hash=None,
                                 move_file=False, strip_file=True):
        """ adds a file to the local file collection, returns a tuple (id, hash,size ) of the LocalFile object
            if only_allowed_hash is set, the file will only be accepted if the hash matches
            strips the file by default of all metadata (provided the file format is recognized)
            returns a tuple (id, hash, size)
        """
        logger.debug("called add_file_from_local_disk, source_path = %s, cwd= %s" % (source_path, os.getcwd()))

        if os.path.getsize(source_path) == 0:
            raise EOFError("File is empty")

        file_hash = file_store.hash_file(source_path)

        if extension[0:1] == '.':
            extension = extension[1:]

        if only_allowed_hash:
            if file_hash != only_allowed_hash:
                logger.error("Allowed hash %s did not match file hash %s, aborting insert" %
                             (only_allowed_hash, file_hash))
                return None, file_hash, None

        if strip_file:
            try:
                new_hash, new_path = self._execute_strip_file(source_path, extension, file_hash,
                                                             only_allowed_hash, move_file)
                if new_hash is not None:
                    move_file = True  # remove the temp file later
                    source_path = new_path
                    file_hash = new_hash

            except ValueError:
                logger.warning("Could not strip file %s, seems to be broken" % source_path)
                return None, None, None

        size = self.file_store.add_file(source_path, file_hash, extension, move_file)
        local_file_id = self.db.add_local_file_exists(file_hash, extension)

        return local_file_id, file_hash, size

    def add_files_from_local_disk(self, file_fields_list):
        result = {}
        for file_fields in file_fields_list:
            f = file_fields

            try:
                file_id, file_hash, size = \
                    self.add_file_from_local_disk(f['source_path'], f['extension'], f['only_allowed_hash'],
                                                  f['move_file'], f['strip_file'])
                if file_id is not None:
                    result[f['source_path']] = True
                else:
                    logger.error("Got error while adding: {}".format(f['source_path']))
                    result[f['source_path']] = False

            except EOFError:
                logger.warning("File {} was empty, ignoring".format(f['source_path']))

        return result

    def _execute_strip_file(self, source_path, extension, file_hash, only_allowed_hash, move_file):
        new_filename, file_hash_after_stripping = \
            file_store.strip_file_to_temp(source_path, extension, remove_original=move_file)

        if new_filename is None:
            return None, None

        if only_allowed_hash:
            if file_hash_after_stripping != file_hash:
                # the file hash changed by stripping but we were ordered to only accept one hash
                # so now we have to update the translation table to change our request behaviour
                logger.info("Hash changed after stripping, recording translation from %s to %s" %
                            (file_hash, file_hash_after_stripping))

                self.db.add_file_hash_translation(file_hash, file_hash_after_stripping)

        return file_hash_after_stripping, new_filename


def _calculate_effective_hash(source_path, extension_without_dot):
    strip_output = cStringIO.StringIO()

    if file_store.strip_file(source_path, extension_without_dot, strip_output):
        strip_output.seek(0)
        return file_store.hash_stream(strip_output)
    else:
        # hash the original file
        return file_store.hash_file(source_path)

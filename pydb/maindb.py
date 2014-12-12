import os
import uuid
import hashlib
import shutil
import time
import traceback
import base64
import logging
from tempfile import mkstemp
import sqlite3 as sqlite
import Pyro4

from mergedb import MergeDB
from localdb import LocalDB
from friendsdb import FriendsDB
from foreigndb import ForeignDB
from pydb import FileType, TomeType, pyrosetup, assert_hash
from sqlitedb import Transaction
import ebook_metadata_tools
from contextlib import contextmanager
from network_params import *
import documents
import databases
import disk_usage
import config

logger = logging.getLogger('database')


class MainDB:
    def __init__(self, base_path, schema_path, enable_db_sync=True):
        self.base_path = base_path
        self.schema_path = schema_path

        self.db_dir = os.path.join(base_path, "db")
        if not os.path.exists(self.db_dir):
            os.makedirs(self.db_dir)

        self.foreign_db_dir = os.path.join(self.db_dir, "foreign")
        if not os.path.exists(self.foreign_db_dir):
            os.makedirs(self.foreign_db_dir)

        self.store_dir = os.path.join(base_path, "filestore")
        if not os.path.exists(self.store_dir):
            os.mkdir(self.store_dir)

        self.default_add_fidelity = 50

        self.enable_db_sync = enable_db_sync
        self.local_db = LocalDB(self.db_path("local"), schema_path, enable_db_sync)
        self.merge_db = MergeDB(self.db_path("merge"), schema_path, enable_db_sync=False)
        self.merge_db.add_source(self.local_db)
        self.friends_db = FriendsDB(self.db_path("friends"), schema_path)

        self.foreign_dbs = {}
        self._load_foreign_dbs()

        logger.info("DBs initialized")

    def db_path(self, db_name):
        return os.path.join(self.db_dir, db_name + ".db")

    def file_store_disk_usage(self):
        total, used, free = disk_usage.disk_usage(self.store_dir)
        return total, used, free

    def _add_foreign_db(self, friend_id):
        logger.info("Loading foreign db for friend %d" % friend_id)
        foreign_db_path = self.db_path(os.path.join("foreign", str(friend_id)))
        db = ForeignDB(foreign_db_path, self.schema_path, friend_id, enable_db_sync=self.enable_db_sync)
        self.foreign_dbs[friend_id] = db
        self.merge_db.add_source(db)

    def _remove_foreign_db(self, friend_id):
        db = self.foreign_dbs[friend_id]
        self.merge_db.remove_source(db)
        del self.foreign_dbs[friend_id]

    def _load_foreign_dbs(self):
        for db in self.foreign_dbs.itervalues():
            self.merge_db.remove_source(db)
            db.close()

        self.foreign_dbs = {}
        friends = self.get_friends()
        for friend in friends:
            friend_id = friend['id']
            self._add_foreign_db(friend_id)

    # noinspection PyMethodMayBeStatic
    def ping(self):
        """ returns a simple string to test whether the connection is working and the server is running """
        return "pong"

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

    def get_merge_statistics(self):
        """ returns a dictionary of merge.db statistics: authors, tomes, files """
        return self.merge_db.get_statistics()

    def get_used_languages(self):
        """ returns a list of principal languages used in the tomes which are present in the database """
        return self.merge_db.get_used_languages()

    def get_tome_statistics(self):
        """ returns a dictionary of merge.db tome statistics:
        first level: language, second level fiction/nonfiction, values: count """
        return self.merge_db.get_tome_statistics()

    def get_local_statistics(self):
        """ returns a dictionary of local.db statistics: authors, tomes, files, local_files """
        return self.local_db.get_statistics()

    def get_tome_authors(self, tome_id):
        """ returns a list of author dicts for all authors linked to a tome, in order of priority """
        return self.merge_db.get_tome_authors(tome_id)

    def get_tome_files(self, tome_id, include_local_file_info=False, file_type=FileType.Content):
        result = self.merge_db.get_tome_files(tome_id, file_type)

        if include_local_file_info:
            for file_info in result:
                self._add_local_file_info(file_info)

        return result

    def get_best_relevant_cover_available(self, tome_id):
        covers = self.merge_db.get_tome_files(tome_id, FileType.Cover)
        for cover in covers:
            if cover['fidelity'] >= Min_Relevant_Fidelity:
                local_file = self.local_db.get_local_file_by_hash(cover['hash'])
                if local_file:
                    return cover

    def find_tomes_by_title(self, title, principal_language, authors_filter=None, subtitle_filter=None):
        """ finds tomes by title """
        return self.merge_db.find_tomes_by_title(title, principal_language, authors_filter, subtitle_filter)

    def find_authors(self, author_name):
        """ finds a author by name or pseudonym """
        return self.merge_db.find_authors(author_name)

    def get_tome_file(self, tome_id, file_hash):
        """ returns a tome file link entry or None if not found"""
        return self.merge_db.get_tome_file(tome_id, file_hash)

    def get_tome_files_by_hash(self, file_hash):
        """ returns a list of tome file links associated with this file hash """
        return self.merge_db.get_tome_files_by_hash(file_hash)

    def get_tome_tags(self, tome_id):
        """ returns a dictionary of tag_fields for all tags linked to the given tome """
        return self.merge_db.get_tome_tags(tome_id)

    def get_file_contents_base64(self, file_hash):
        """ returns a string containing the file identified by hash. The data is encoded using base64 """

        file_ext = self.get_file_extension(file_hash)
        if file_ext is not None:
            cache_path = self._calculate_cache_path(file_hash) + '.' + file_ext
            logger.debug("Trying to open file " + cache_path + " for reading")

            with open(cache_path, 'rb') as f:
                data = base64.b64encode(f.read())
                return data

    def get_local_file_path(self, file_hash):
        """ returns a string containing the path to the file identified by hash or None """
        file_ext = self.get_file_extension(file_hash)
        if file_ext is not None:
            cache_path = self._calculate_cache_path(file_hash) + '.' + file_ext
            return os.path.abspath(cache_path)

    def get_file_extension(self, file_hash):
        """ returns a string containing the file extension of the file identified by hash. """
        file_info = self.local_db.get_local_file_by_hash(file_hash)
        if file_info is not None:
            return file_info["file_extension"]

    def get_local_file_size(self, file_hash):
        """ returns a the file size of the file identified by hash if it's available locally. """
        fp = self.get_local_file_path(file_hash)
        if not fp:
            return None

        return os.path.getsize(fp)

    def get_all_file_hash_translation_sources(self, target_hash):
        """ returns a list of all hashes that translate to target_hash (including target_hash) """
        return self.local_db.get_all_file_hash_translation_sources(target_hash)

    def get_tome(self, tome_id):
        """ returns a tome from the merge table identified by id """
        return self.merge_db.get_tome(tome_id)

    def _add_local_file_info(self, file_info):
        file_hash = file_info['hash']
        local_file = self.local_db.get_local_file_by_hash(file_hash)
        file_info['has_local_copy'] = bool(local_file)

    def get_tome_by_guid(self, tome_guid):
        """ returns a tome from the merge table identified by guid """
        return self.merge_db.get_tome_by_guid(tome_guid)

    def get_tome_document(self, tome_id, ignore_fidelity_filter=False):
        tome = self.get_tome(tome_id)
        if tome is None:
            return None
        return self.get_tome_document_by_guid(tome['guid'], ignore_fidelity_filter)

    def get_tome_document_by_guid(self, tome_guid, ignore_fidelity_filter=False,
                                  include_author_detail=False, keep_id=False):
        """ returns the full tome document (including files, tags..) for a given tome identified by id
            a tome document may be empty (only guid, no title key) if the fidelity is below the relevance threshold
        """
        return self.merge_db.get_tome_document_by_guid(tome_guid, ignore_fidelity_filter,
                                                       include_author_detail=include_author_detail, keep_id=keep_id)

    def get_local_tome_document_by_guid(self, tome_guid, ignore_fidelity_filter=False, include_author_detail=False):
        """ returns the local tome document (including files, tags..) for a given tome identified by id
            a tome document may be empty (only guid, no title key) if the fidelity is below the relevance threshold
        """
        return self.local_db.get_tome_document_by_guid(tome_guid, ignore_fidelity_filter,
                                                       include_author_detail=include_author_detail)

    def get_tome_document_with_local_overlay_by_guid(self, tome_guid,
                                                     ignore_fidelity_filter=False,
                                                     include_local_file_info=False,
                                                     include_author_detail=False):
        """ returns the full tome document (including files, tags..) for a given tome identified by id
            a tome document may be empty (only guid, no title key) if the fidelity is below the relevance threshold.
            After getting the full tome document, entries which have a local entry will be replaced if their fidelity
            is of larger magnitude.
            The result will also contain the tome id
        """
        
        merge_tome = self.get_tome_document_by_guid(tome_guid, ignore_fidelity_filter,
                                                    include_author_detail=include_author_detail, keep_id=True)
        if 'title' not in merge_tome:
            return merge_tome                                                    
                                                    
        local_tome = self.get_local_tome_document_by_guid(tome_guid, ignore_fidelity_filter,
                                                          include_author_detail=include_author_detail)

        result = documents.overlay_document(merge_tome, local_tome)

        if include_local_file_info:
            for file_info in result['files']:
                self._add_local_file_info(file_info)
        
        return result

    def get_latest_tome_related_change(self, tome_guid):
        """ returns the id of the friend (or 0 for "local"), the date of the latest change
            affecting the merge db entry of the tome.
            Also contains the name of the table affected.
            Result is a dictionary {friend_id, last_modification_date, table_name}
        """

        # 1. find newest effective change
        tome = self.merge_db.get_tome_by_guid(tome_guid)
        if tome is None:
            return None
        tome_id = tome['id']

        tables = databases.tables_with_tome_link
        tables.append("tomes")
        change_dates = []
        for t in tables:
            if t == 'tomes':
                item = self.merge_db.get_tome(tome_id)
            else:
                item = self.merge_db.get_item_linked_to_tome_by_tome_id(t, tome_id)
            if item is not None:
                change_date = item['last_modification_date']
                change_dates.append((change_date, t))
        newest_change = max(change_dates, key=lambda x: x[0])

        # @todo: this is not right as we have to distinguish between many items linked to the tome and not only one
        items = []
        for friend_id, foreign_db in self.foreign_dbs.iteritems():
            tome = foreign_db.get_tome_by_guid(tome_guid)
            if tome:
                tome_id = tome['id']
                # \todo using t here is definitive wrong
                if t == 'tomes':
                    item = tome
                else:
                    item = foreign_db.get_item_linked_to_tome_by_tome_id(newest_change[1], tome_id)

                if item is not None:
                    item['friend_id'] = friend_id
                    items.append(item)

        tome = self.local_db.get_tome_by_guid(tome_guid)
        if tome is not None:
            tome_id = tome['id']

            if t == 'tomes':
                local_item = tome
            else:
                local_item = self.local_db.get_item_linked_to_tome_by_tome_id(newest_change[1], tome_id)

            if local_item is not None:
                local_item['friend_id'] = 0
                items.append(local_item)

        max_fidelity_item = max(items, key=lambda x: x['fidelity'])

        if max_fidelity_item is None:
            return None

        result = {'friend_id': max_fidelity_item['friend_id'],
                  'last_modification_date': max_fidelity_item['last_modification_date'],
                  'table_name': t}
        return result

    def get_debug_info_for_tome_by_guid(self, tome_guid):
        """ returns tome documents for all databases (local, merge, all foreign) to improve network debugging
        """
        merge_doc = self.merge_db.get_tome_document_by_guid(tome_guid, ignore_fidelity_filter=True)
        local_doc = self.local_db.get_tome_document_by_guid(tome_guid, ignore_fidelity_filter=True)

        friends_docs = {}
        for friend_id, foreign_db in self.foreign_dbs.iteritems():
            friends_docs[friend_id] = foreign_db.get_tome_document_by_guid(tome_guid, ignore_fidelity_filter=True)

        result = {
            'merge_doc': merge_doc,
            'local_doc': local_doc,
            'friends': friends_docs
        }

        return result

    def get_author(self, author_id):
        """ returns a author from the merge table identified by id """
        return self.merge_db.get_author(author_id)

    def get_author_by_guid(self, author_guid):
        """ returns a author from the merge table identified by guid """
        return self.merge_db.get_author_by_guid(author_guid)

    def get_author_document_by_guid(self, author_guid, ignore_fidelity_filter=False, keep_id=False):
        """ returns the full author document (including pseudonyms..) for a given author identified by id
            an author document may be empty (only guid, no name key) if the fidelity is below the relevance threshold
        """
        return self.merge_db.get_author_document_by_guid(author_guid, ignore_fidelity_filter, keep_id)

    def get_local_author_document_by_guid(self, author_guid, ignore_fidelity_filter=False):
        """ returns the local database author document (including pseudonyms..) for a given author identified by id
            an author document may be empty (only guid, no name key) if the fidelity is below the relevance threshold
        """
        return self.local_db.get_author_document_by_guid(author_guid, ignore_fidelity_filter)

    def get_author_document_with_local_overlay_by_guid(self, author_guid, ignore_fidelity_filter=False):
        """ returns the full author document for a given tome identified by id
            an author document may be empty (only guid, no name key) if the fidelity is below the relevance threshold.
            After getting the full author document, entries which have a local entry will be replaced if their fidelity
            is of larger magnitude
        """
        merge_author = self.get_author_document_by_guid(author_guid, ignore_fidelity_filter, keep_id=True)
        local_author = self.get_local_author_document_by_guid(author_guid, ignore_fidelity_filter)
        
        result = documents.overlay_document(merge_author, local_author)
        
        return result

    def document_modification_date_by_guid(self, doc_type, guid):
        return self.merge_db.document_modification_date_by_guid(doc_type, guid)

    def add_author(self, name, guid=None, date_of_birth=None, date_of_death=None, fidelity=None):
        """ adds a new author, generating a guid, returns the id of the author """
        if not fidelity:
            fidelity = self.default_add_fidelity

        if not guid:
            guid = self.generate_guid()

        self.local_db.add_author(guid, name, fidelity, date_of_birth=date_of_birth, date_of_death=date_of_death)
        self.merge_db.request_author_update(guid)
        author = self.merge_db.get_author_by_guid(guid)

        _update_search_index()

        return author['id']

    def _merge_db_author_id_to_local_db_author_id(self, merge_db_author_id):
        """ converts a merge db author id to a local db author id, creating the local db entry if necessary """

        merge_db_author = self.merge_db.get_author(merge_db_author_id)
        guid = merge_db_author['guid']

        local_db_author = self.local_db.get_author_by_guid(guid)
        if local_db_author:
            return local_db_author['id']

        return self.local_db.add_author(guid, merge_db_author['name'],
                                        date_of_birth=merge_db_author['date_of_birth'],
                                        date_of_death=merge_db_author['date_of_death'],
                                        fidelity=_auto_create_fidelity(merge_db_author['fidelity']))

    def _merge_db_tome_id_to_local_db_tome_id(self, merge_db_tome_id):
        """ converts a merge db tome id to a local db tome id, creating the local db entry if necessary """

        merge_db_tome = self.merge_db.get_tome(merge_db_tome_id)
        guid = merge_db_tome['guid']

        local_db_tome = self.local_db.get_tome_by_guid(guid)
        if local_db_tome:
            return local_db_tome['id']

        # convert author ids of merge db to local
        merge_db_author_ids = self.merge_db.get_tome_author_ids(merge_db_tome_id)
        local_db_author_ids = [self._merge_db_author_id_to_local_db_author_id(a) for a in merge_db_author_ids]

        t = merge_db_tome
        return self.local_db.add_tome(guid, t['title'], t['principal_language'],
                                      local_db_author_ids, _auto_create_fidelity(t['fidelity']),
                                      publication_year=t['publication_year'], edition=t['edition'],
                                      subtitle=t['subtitle'], tome_type=t['type'])

    def add_tome(self, title, principal_language, author_ids, guid=None, publication_year=None, edition=None,
                 subtitle=None, tome_type=TomeType.Unknown, fidelity=None, tags_values=None):
        """ adds a new tome, generating a guid. returns a tome_id
            is_fiction: None => unknown, True => fiction, False=>non_fiction
        """
        logging.debug("Called add_tome")

        if not fidelity:
            fidelity = self.default_add_fidelity

        # prepare the local information about the author
        with Transaction(self.local_db):
            local_db_author_ids = []
            for merge_db_author_id in author_ids:
                local_author_id = self._merge_db_author_id_to_local_db_author_id(merge_db_author_id)
                local_db_author_ids.append(local_author_id)

            # insert the tome
            if not guid:
                guid = self.generate_guid()

            tome_id = self.local_db.add_tome(guid, title, principal_language, local_db_author_ids, fidelity,
                                             publication_year=publication_year, edition=edition, subtitle=subtitle,
                                             tome_type=tome_type)

            if tags_values is not None:
                self.local_db.add_tags_to_tome(tome_id, tags_values, fidelity)

        # notify merge db
        with Transaction(self.merge_db):
            self.merge_db.request_tome_update(guid)
            self.merge_db.request_tome_authors_update(guid)

            if tags_values is not None:
                self.merge_db.request_tome_tag_update(guid)

        tome = self.merge_db.get_tome_by_guid(guid)

        _update_search_index()

        return tome['id']

    def _apply_file_hash_translation(self, source_hash, target_hash):
        """ goes through all databases making sure that all instances of source_hash
        have been replaced by target_hash """

        affected_tome_guids = set()

        # update local db
        affected_tome_ids = self.local_db.apply_file_hash_translation(source_hash, target_hash)
        logger.info("%d tomes affected in local db", len(affected_tome_ids))
        affected_tome_guids.update([self.local_db.tome_id_to_guid(tome_id) for tome_id in affected_tome_ids])

        # update foreign dbs
        for friend_id, db in self.foreign_dbs.iteritems():
            affected_tome_ids = db.apply_file_hash_translation(source_hash, target_hash)
            affected_tome_guids.update([db.tome_id_to_guid(tome_id) for tome_id in affected_tome_ids])
            logger.info("%d tomes affected in friend db %d", len(affected_tome_ids), friend_id)

        with Transaction(self.merge_db):
            for affected_tome_guid in affected_tome_guids:
                self.merge_db.request_tome_file_update(affected_tome_guid)

    def add_files_from_local_disk(self, file_fields_list):
        result = {}
        with Transaction(self.merge_db):
            with Transaction(self.local_db):
                for friend_id, db in self.foreign_dbs.iteritems():
                    db.begin()

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

                for friend_id, db in self.foreign_dbs.iteritems():
                    db.commit()
        return result

    def is_local_file_known(self, source_path, extension_without_dot):
        """ returns true if the file specified by source_path is already attached to at least one tome
            raises an ValueError if the file is broken
        """

        # @todo we can do this in memory, too
        temp_file, effective_hash = _strip_file_to_temp(source_path, extension_without_dot)
        if temp_file is None:
            effective_hash = _hash_file(source_path)
        else:
            os.remove(temp_file)

        used_links = self.merge_db.get_tome_files_by_hash(effective_hash)
        return bool(used_links)

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

        file_hash = _hash_file(source_path)

        if extension[0:1] == '.':
            extension = extension[1:]

        if only_allowed_hash:
            if file_hash != only_allowed_hash:
                logger.error("Allowed hash %s did not match file hash %s, aborting insert" %
                             (only_allowed_hash, file_hash))
                return None, file_hash, None

        if strip_file:
            try:
                new_filename, file_hash_after_stripping = \
                    _strip_file_to_temp(source_path, extension, remove_original=move_file)
                if new_filename is not None:
                    if only_allowed_hash:
                        if file_hash_after_stripping != file_hash:
                            # the file hash changed by stripping but we were ordered to only accept one hash
                            # so now we have to update the translation table to change our request behaviour
                            logger.info("Hash changed after stripping, recording translation from %s to %s" %
                                        (file_hash, file_hash_after_stripping))
                            self.local_db.add_file_hash_translation(file_hash, file_hash_after_stripping)
                            self._apply_file_hash_translation(file_hash, file_hash_after_stripping)

                    file_hash = file_hash_after_stripping
                    source_path = new_filename
                    move_file = True  # remove the temp file later

            except ValueError:
                logger.warning("Could not strip file %s, seems to be broken" % source_path)
                return None, None, None

        size = os.path.getsize(source_path)
        if size == 0:
            raise ValueError("File is empty after stripping")

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
                old_hash = _hash_file(cache_path)
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
                old_hash = _hash_file(cache_path)
                if old_hash != file_hash:
                    logger.info(u"Old hash in file_store {} doesn't match the actual hash {} overwriting."
                                .format(old_hash, file_hash))
                    shutil.copyfile(source_path, cache_path)

        # \todo check hash after copying to ensure it worked (e.g. disk full)
        if size != os.path.getsize(cache_path):
            raise Exception(u"File sizes after insert do not match: {} bytes in file to insert, "
                            "{} bytes in store. Cache path is {}".format(size, os.path.getsize(cache_path), cache_path))

        local_file_id = self.local_db.add_local_file(file_hash, extension)
        self.merge_db.insert_local_file({'hash': file_hash, 'file_extension': extension})

        if move_file and os.path.exists(source_path):
            os.remove(source_path)

        return local_file_id, file_hash, size

    def link_tome_to_file(self, tome_id, local_file_hash, local_file_size, file_extension,
                          file_type=FileType.Content, fidelity=None):
        """ creates a link between a tome and a local file """
        if not fidelity:
            fidelity = self.default_add_fidelity

        local_db_tome_id = self._merge_db_tome_id_to_local_db_tome_id(tome_id)
        merge_db_tome = self.merge_db.get_tome(tome_id)
        guid = merge_db_tome['guid']

        self.local_db.add_tome_file_link(fidelity, file_extension, file_type,
                                         local_db_tome_id, local_file_hash, local_file_size)
        self.merge_db.request_tome_file_update(guid)

    def remove_local_tome_links_to_missing_files(self):
        """ removes all local info about tome<->file links for files we do not have
        can be used for clean up purposes on non-sparse nodes - do not use on metadata-only-nodes
        """

        file_links_without_content = self.local_db.get_file_links_to_missing_files()

        count = 0
        with Transaction(self.local_db):
            with Transaction(self.merge_db):
                for f in file_links_without_content:
                    tome_id = f['tome_id']
                    self.local_db.remove_file_link(tome_id, f['hash'])
                    tome = self.local_db.get_tome(tome_id)
                    logger.info("Removing file {} from tome {}".format(f['hash'], tome['title']))
                    self.merge_db.request_tome_file_update(tome['guid'])
                    count += 1
        return count

    def link_tome_to_author(self, tome_id, author_id, author_order, fidelity):
        fidelity = float(fidelity)
        author_order = float(author_order)

        local_db_tome_id = self._merge_db_tome_id_to_local_db_tome_id(tome_id)
        local_db_author_id = self._merge_db_author_id_to_local_db_author_id(author_id)

        cur = self.local_db.con.cursor()
        cur.execute("INSERT OR IGNORE INTO tomes_authors "
                    "(tome_id, author_id, author_order, fidelity, last_modification_date) VALUES(?,?,?,?,?)",
                    (local_db_tome_id, local_db_author_id, author_order, fidelity, time.time()))

        merge_db_tome = self.merge_db.get_tome(tome_id)
        tome_guid = merge_db_tome['guid']

        self.merge_db.request_tome_authors_update(tome_guid)

    def add_tags_to_tome(self, tome_id, tag_value_list, fidelity):
        local_db_tome_id = self._merge_db_tome_id_to_local_db_tome_id(tome_id)
        merge_db_tome = self.merge_db.get_tome(tome_id)
        guid = merge_db_tome['guid']

        with Transaction(self.local_db):
            self.local_db.add_tags_to_tome(local_db_tome_id, tag_value_list, fidelity)

        self.merge_db.request_tome_tag_update(guid)
        _update_search_index()

    def _add_synopsis_to_tome(self, guid, content, local_db_tome_id, fidelity=None):
        """ adds a new synopsis, returns the id of the synopsis """
        if not fidelity:
            fidelity = self.default_add_fidelity
        synopsis_id = self.local_db.add_synopsis_to_tome(guid, content, local_db_tome_id, fidelity)
        return synopsis_id

    def add_friend(self, name):
        """ adds a fried to the database, returning the id """
        friend_id = self.friends_db.add_friend(name)
        self._add_foreign_db(friend_id)
        return friend_id

    def remove_friend(self, friend_id):
        """ removes a friend and from database """
        self.friends_db.remove_friend(friend_id)
        self._remove_foreign_db(friend_id)

    def get_friends(self):
        """ returns a list of friend dictionaries """
        return self.friends_db.get_friends()

    def get_friend(self, friend_id):
        """ returns the dictionary of the friend given by id """
        return self.friends_db.get_friend(friend_id)

    def get_friend_by_name(self, name):
        """ returns the dictionary of the friend given by name """
        return self.friends_db.get_friend_by_name(name)

    def set_friend_name(self, friend_id, name):
        self.friends_db.set_name(friend_id, name)

    def set_friend_can_connect_to(self, friend_id, can_connect_to):
        self.friends_db.set_can_connect_to(friend_id, can_connect_to)

    def set_friend_last_query_dates(self, friend_id, query_date_authors, query_date_tomes):
        db = self.foreign_dbs[friend_id]
        db.set_last_query_dates(query_date_authors, query_date_tomes)

    def get_friend_last_query_dates(self, friend_id):
        db = self.foreign_dbs[friend_id]
        return db.get_last_query_dates()

    def load_author_documents_from_friend(self, friend_id, author_docs):
        db = self.foreign_dbs[friend_id]

        with Transaction(db):
            for original_author_doc in author_docs:
                author_doc = documents.prepare_author_document(original_author_doc)
                author_guid = author_doc['guid']

                if 'name' not in author_doc:  # delete request
                    db.delete_author_by_guid(author_guid)
                else:
                    author_doc['last_modification_date'] = time.time()
                    author_doc['fidelity'] = _effective_friend_fidelity(float(author_doc['fidelity']))
                    db.apply_author_document(author_doc)

        with Transaction(self.merge_db):
            for author_doc in author_docs:
                author_guid = author_doc['guid']
                self.merge_db.request_complete_author_update(author_guid)

        _update_search_index()

    def load_tome_documents_from_friend(self, friend_id, tome_docs):
        db = self.foreign_dbs[friend_id]

        with Transaction(db):
            for original_tome_doc in tome_docs:
                tome_doc = documents.prepare_tome_document(original_tome_doc, self.local_db)
                tome_guid = tome_doc['guid']

                if 'title' not in tome_doc:  # delete request
                    db.delete_tome_by_guid(tome_guid)
                else:
                    tome_doc['last_modification_date'] = time.time()
                    tome_doc['fidelity'] = _effective_friend_fidelity(tome_doc['fidelity'])

                    for a in tome_doc['authors']:
                        a['fidelity'] = _effective_friend_fidelity(a['fidelity'])
                    for t in tome_doc['tags']:
                        t['fidelity'] = _effective_friend_fidelity(t['fidelity'])
                    for f in tome_doc['files']:
                        f['fidelity'] = _effective_friend_fidelity(f['fidelity'])
                    for s in tome_doc['synopses']:
                        s['fidelity'] = _effective_friend_fidelity(s['fidelity'])
                    for s in tome_doc['fusion_sources']:
                        s['fidelity'] = _effective_friend_fidelity(s['fidelity'])

                    try:
                        logger.debug("Trying to apply tome %s from friend %d." % (tome_guid, friend_id))
                        logger.debug("Content: %s", repr(tome_doc))
                        db.apply_tome_document(tome_doc)
                    except KeyError, e:
                        friend = self.get_friend(friend_id)
                        logger.error(
                            "Caught KeyError %s while trying to insert tome %s from friend %s (%d). """
                            "Skipping tome import.\nTB %s" % (
                                repr(e), tome_guid, friend['name'], friend_id, traceback.format_exc()))
                    except sqlite.IntegrityError, e:
                        friend = self.get_friend(friend_id)
                        logger.error(
                            "Caught IntegrityError %s while trying to insert tome %s from friend %s (%d). """
                            "Skipping tome import.\nTB %s" % (
                                repr(e), tome_guid, friend['name'], friend_id, traceback.format_exc()))
                        raise

        with Transaction(self.merge_db):
            for tome_doc in tome_docs:
                tome_guid = tome_doc['guid']
                logger.info("Triggering merge db update update for tome %s" % tome_guid)
                logger.debug("Content: %s", repr(tome_doc))
                self.merge_db.request_complete_tome_update(tome_guid, include_fusion_source_update=True)

        _update_search_index()

    def load_own_author_document(self, author_doc):
        with Transaction(self.local_db):
            prepared_author_doc = documents.prepare_author_document(author_doc)
            author_guid = prepared_author_doc['guid']
            self.local_db.apply_author_document(prepared_author_doc)

        with Transaction(self.merge_db):
            self.merge_db.request_complete_author_update(author_guid)

        _update_search_index()

    def load_own_tome_document(self, tome_doc):
        with Transaction(self.local_db):
            tome_guid = tome_doc['guid']

            prepared_tome_doc = documents.prepare_tome_document(tome_doc, self.local_db)

            # check that all referenced authors are actually present in local db (not only merge)
            for author_link_info in prepared_tome_doc['authors']:
                author_guid = author_link_info['guid']
                author_local = self.local_db.get_author_by_guid(author_guid)
                if not author_local:
                    author_merge = self.merge_db.get_author_by_guid(author_guid)

                    if author_merge:
                        self._merge_db_author_id_to_local_db_author_id(author_merge['id'])  # create the author in local
                    else:
                        raise KeyError("No author with guid %s for tome %s found, skipping tome edit " %
                                       (author_guid, tome_guid))

            self.local_db.apply_tome_document(prepared_tome_doc)

        with Transaction(self.merge_db):
            self.merge_db.request_complete_tome_update(tome_guid, include_fusion_source_update=True)

        _update_search_index()

    def get_tomes_by_author(self, author_id):
        return self.merge_db.get_tomes_by_author(author_id)

    def get_all_tomes(self):
        return list(self.merge_db.get_all_tomes())

    def get_all_tome_ids(self):
        return self.merge_db.get_all_tome_ids()

    def get_all_tome_guids(self):
        return self.merge_db.get_all_tome_guids()

    def get_all_authors(self):
        return self.merge_db.get_all_authors()

    def get_all_author_ids(self):
        return self.merge_db.get_all_author_ids()

    def get_all_author_guids(self):
        return self.merge_db.get_all_author_guids()

    def get_tome_fusion_target_guid(self, source_tome_guid):
        """ returns the target guid if the given tome_guid is an source for an active tome fusion
        """
        return self.merge_db.get_tome_fusion_target_guid(source_tome_guid)

    def get_author_fusion_target_guid(self, source_author_guid):
        """ returns the target guid if the given author_guid is an source for an active author fusion
        """
        return self.merge_db.get_author_fusion_target_guid(source_author_guid)

    def rebuild_merge_db(self):
        with Transaction(self.merge_db):
            logger.info("Deleting old merge db contents")
            self.merge_db.delete_all()

            logger.info("Rebuilding local file cache")
            for local_file in self.local_db.get_all_local_files():
                self.merge_db.insert_local_file(local_file)

            dbs = [self.local_db] + self.foreign_dbs.values()

            logger.info("Rebuilding authors")
            all_author_guids = set()

            for db in dbs:
                all_author_guids.update([author['guid'] for author in db.get_all_authors()])

            for author_guid in all_author_guids:
                self.merge_db.request_author_update(author_guid)

            logger.info("Rebuilding tomes")
            processed_tome_guids = set()

            for db in dbs:
                tomes = list(db.get_all_tomes())
                for tome in tomes:
                    guid = tome['guid']
                    if guid not in processed_tome_guids:
                        processed_tome_guids.add(guid)
                        self.merge_db.request_complete_tome_update(guid, include_fusion_source_update=True)

            logger.info("Committing")

        _update_search_index()

    def request_complete_tome_update(self, guid):
        self.merge_db.request_complete_tome_update(guid, include_fusion_source_update=True)
        _update_search_index()

    def hard_commit_all(self):
        with collect_transaction_errors("local"):
            self.local_db.commit()
        with collect_transaction_errors("merge"):
            self.merge_db.commit()
        for db in self.foreign_dbs.itervalues():
            with collect_transaction_errors("foreign"):
                db.commit()
        with collect_transaction_errors("friend"):
            self.friends_db.commit()

    def get_file_hashes_to_request(self, max_results=100000):
        min_tome_fidelity = 30
        min_file_fidelity = 30

        max_file_size_bytes = config.max_file_size_to_request_bytes()

        return list(self.merge_db.get_high_fidelity_tome_file_hashes_without_local_file(min_tome_fidelity,
                                                                                        min_file_fidelity,
                                                                                        max_file_size_bytes,
                                                                                        max_results))

    def check_merge_db_for_content_problems(self):
        return self.merge_db.check_for_content_problems()

    def check_databases_for_consistency_problems(self):
        result = {
            'merge_db': self.merge_db.check_for_consistency_problems(),
            'local_db': self.local_db.check_for_consistency_problems()
        }

        for friend_id, db in self.foreign_dbs.iteritems():
            friend = self.get_friend(friend_id)
            friend_key = 'friend_{}'.format(friend['name'])
            result[friend_key] = db.check_for_consistency_problems()
        return result

    def fix_databases(self):
        self.merge_db.update_tomes_without_authors()

    def _get_single_document_change_package(self, document_type, min_modification_date, max_items_to_fetch):
        """ returns a triple (changed_document_guids, new_min_modification_date, was_cut_off """

        cut_off = False
        (changed_items, max_change_date_items) = self.merge_db.get_modified_document_guids(document_type,
                                                                                           max_items_to_fetch,
                                                                                           min_modification_date)
        if len(changed_items) == max_items_to_fetch:
            cut_off = True
            # remove all entries having last_mod_date=max_change_date as we don't know whether there
            # are more which we did not fetch
            changed_items_cutoff = [(guid, mod_date) for (guid, mod_date) in changed_items if
                                    mod_date < max_change_date_items]
            max_change_date_items = max([mod_date for (guid, mod_date) in changed_items_cutoff])
            if not changed_items_cutoff:
                raise Exception(
                    "Unable to create change package: More than %s tome entries have the same change date: %d" % (
                        max_items_to_fetch, max_change_date_items))
            changed_items = changed_items_cutoff

        changed_guids = [guid for (guid, mod_date) in changed_items]

        if max_change_date_items < 0:
            max_change_date_items = min_modification_date

        return changed_guids, max_change_date_items, cut_off

    def get_document_change_package(self, min_modification_date_authors, min_modification_date_tomes):
        """ returns a tuple
        (changed_author_guids, changed_tome_guids, new_min_modification_date_authors,
        new_min_modification_date_tomes)
        containing changes that have occurred since min_modification_date (inclusively).
        new_min_modification_date_xx is guaranteed to be larger than min_modification_date_xx iff
        there is at least one author/tome guid returned
        """

        max_items_to_fetch = 10001  # most of the time we remove the last one, so order one too much

        changed_author_guids, new_min_mod_date_authors, authors_cut_off = \
            self._get_single_document_change_package('author', min_modification_date_authors, max_items_to_fetch)

        changed_tome_guids = []
        new_min_mod_date_tomes = min_modification_date_tomes

        if not authors_cut_off:
            changed_tome_guids, new_min_mod_date_tomes, tomes_cut_off = self._get_single_document_change_package(
                'tome', min_modification_date_tomes, max_items_to_fetch - len(changed_tome_guids))

        return changed_author_guids, changed_tome_guids, new_min_mod_date_authors, new_min_mod_date_tomes

    def changed_documents_count(self, min_modification_date_authors, min_modification_date_tomes):
        number_changed_authors = self.merge_db.changed_documents_count('author', min_modification_date_authors)
        number_changed_tomes = self.merge_db.changed_documents_count('tome', min_modification_date_tomes)
        return number_changed_authors, number_changed_tomes

    def get_tome_document_timeline(self, max_items_to_fetch):
        """ returns a list of tuples ( tome_guid, last_mod_date)"""
        doc_list = self.merge_db.get_newest_modified_document_guids('tome', max_items_to_fetch)
        return doc_list

    # concept of generic author
    # if there is more than one author with the same name, we'll add to the one without a
    # date_of_birth (creating it if it does not exist) unless we can identify the correct author
    # using e.g. a tome title
    def find_or_create_author(self, author_name, fidelity):
        """ returns a merge db author id """
        author_candidates = self.find_authors(author_name)

        if len(author_candidates) == 1:  # we have only one candidate, use it
            return author_candidates[0]['id']

        if len(author_candidates) == 0:  # no candidates, create it
            author_id = self.add_author(author_name, fidelity=fidelity)
            return author_id

        # more than one author, find/create the generic one
        for author in author_candidates:
            if author['date_of_birth'] is None and author['date_of_death'] is None:
                return author['id']

        # create it
        return self.add_author(author_name, fidelity=fidelity)

    # before creating authors / tomes, check the merge db as there might already be data
    def find_or_create_authors(self, author_names, fidelity):
        """ returns a list of merge db author ids  """
        author_ids = [self.find_or_create_author(author_name, fidelity) for author_name in author_names]
        return author_ids

    def find_or_create_tome(self, title, language, author_ids, subtitle, tome_type, fidelity, publication_year=None,
                            tags_values=None):
        tome_candidates = self.find_tomes_by_title(title, language, author_ids, subtitle)

        if len(tome_candidates) == 1:  # one tome, use it
            return tome_candidates[0]['id']

        if len(tome_candidates) > 1:  # more than one tome candidate

            if publication_year:
                # find the one matching publication year and having empty edition
                for tome_fields in tome_candidates:
                    if tome_fields['edition'] is None and tome_fields['publication_year'] == publication_year:
                        return tome_fields['id']

                # now search for all matching the pub year
                for tome_fields in tome_candidates:
                    if tome_fields['publication_year'] == publication_year:
                        return tome_fields['id']

            # find/create the generic one
            for tome_fields in tome_candidates:
                if tome_fields['edition'] is None and tome_fields['publication_year'] is None:
                    return tome_fields['id']

        return self.add_tome(title, language, author_ids, subtitle=subtitle, fidelity=fidelity, tome_type=tome_type,
                             publication_year=publication_year, tags_values=tags_values)

    def get_tome_fidelities(self, tome_id):
        """ returns a tuple (effective_fidelity, local_fidelity, min_foreign_fidelity, max_foreign_fidelity) of
        fidelities for a given tome. values might be None if not available """

        merge_db_tome = self.merge_db.get_tome(tome_id)
        tome_guid = merge_db_tome['guid']
        effective_fidelity = merge_db_tome['fidelity']

        local_db_tome = self.local_db.get_tome_by_guid(tome_guid)
        local_fidelity = None
        if local_db_tome:
            local_fidelity = local_db_tome['fidelity']

        min_foreign_fidelity = None
        max_foreign_fidelity = None

        for friend_id, db in self.foreign_dbs.iteritems():
            friend_tome = db.get_tome_by_guid(tome_guid)

            if friend_tome:
                friend_tome_fidelity = friend_tome['fidelity']
                if min_foreign_fidelity is None:
                    min_foreign_fidelity = max_foreign_fidelity = friend_tome_fidelity
                else:
                    min_foreign_fidelity = min(min_foreign_fidelity, friend_tome_fidelity)
                    max_foreign_fidelity = max(max_foreign_fidelity, friend_tome_fidelity)

        return effective_fidelity, local_fidelity, min_foreign_fidelity, max_foreign_fidelity

    def get_random_tomes(self, number_tomes):
        return list(self.merge_db.get_random_tomes(number_tomes))

    def calculate_required_tome_fidelity(self, tome_id):
        """ returns the minimum fidelity required to outbid all direct friends """

        merge_db_item = self.merge_db.get_tome(tome_id)
        item_guid = merge_db_item['guid']

        items_from_friends = []
        for friend_id, foreign_db in self.foreign_dbs.iteritems():
            friend_item = foreign_db.get_tome_by_guid(item_guid)
            if friend_item:
                items_from_friends.append(friend_item)

        return documents.calculate_required_edit_fidelity(merge_db_item, items_from_friends)

    def calculate_required_author_fidelity(self, author_id):
        """ returns the minimum fidelity required to outbid all direct friends """

        merge_db_item = self.merge_db.get_author(author_id)
        item_guid = merge_db_item['guid']

        items_from_friends = []
        for friend_id, foreign_db in self.foreign_dbs.iteritems():
            friend_item = foreign_db.get_author_by_guid(item_guid)
            if friend_item:
                items_from_friends.append(friend_item)

        return documents.calculate_required_edit_fidelity(merge_db_item, items_from_friends)

    # noinspection PyMethodMayBeStatic
    def generate_guid(self):
        return uuid.uuid4().hex

    def fuse_tomes(self, source_guid, target_guid):
        """ fuses two the tome identified by source_guid into target_guid -
         so that afterwards the fused tome has the tome data fiven by target_guid) """
        source_tome = self.get_tome_by_guid(source_guid)
        target_tome = self.get_tome_by_guid(target_guid)

        data_tome = target_tome

        fidelity = Default_Manual_Fidelity

        if target_guid < source_guid:  # this is not allowed by db, switch
            source_guid, target_guid = target_guid, source_guid
            source_tome, target_tome = target_tome, source_tome

        new_tome_doc = self.get_tome_document_by_guid(target_guid)
        new_tome_doc['fusion_sources'].append({'source_guid': source_guid, 'fidelity': fidelity})

        if data_tome != target_tome:  # copy data from data tome over
            for key, value in data_tome.iteritems():
                if key in new_tome_doc:
                    if key.lower() != "guid":
                        new_tome_doc[key] = data_tome[key]

        self.load_own_tome_document(new_tome_doc)


def _hash_stream(stream):
    chunk_size_bytes = 100*1000

    hash_algo = hashlib.sha256()
    buf = stream.read(chunk_size_bytes)
    while buf:
        hash_algo.update(buf)
        buf = stream.read(chunk_size_bytes)
    return hash_algo.hexdigest()


def _hash_file(path):
    return _hash_stream(open(path, 'rb'))


def _update_search_index():
    # noinspection PyUnresolvedReferences
    try:
        index_server = pyrosetup.indexserver()
        index_server.update_index()
    except Pyro4.errors.CommunicationError, e:
        logger.error("Unable to connect to index_server: %s" % e)


def _effective_friend_fidelity(friend_fidelity, specific_friend_deduction=Friend_Fidelity_Deduction):
    f = friend_fidelity
    f = min(f, 100)
    f = max(f, -100)

    if f >= 0:
        return max(0, f - specific_friend_deduction)
    else:
        return min(0, f + specific_friend_deduction)


def _auto_create_fidelity(merge_db_fidelity):
    f = merge_db_fidelity

    if f > Fidelity_Deduction_Auto_Create:
        return f - Fidelity_Deduction_Auto_Create

    if f < -Fidelity_Deduction_Auto_Create:
        return f + Fidelity_Deduction_Auto_Create

    return 0


def _strip_file_to_temp(source_path, extension_without_dot, remove_original=False):
    (handle, filename_stripped) = mkstemp(suffix='.' + extension_without_dot)
    logger.info("Writing to file %s" % filename_stripped)
    f = os.fdopen(handle, "w")

    if ebook_metadata_tools.strip_file(source_path, extension_without_dot, f):
        f.close()
        if remove_original:
            os.remove(source_path)
        file_hash_after_stripping = _hash_file(filename_stripped)
        return filename_stripped, file_hash_after_stripping

    else:
        f.close()
        os.remove(filename_stripped)
        return None, None


@contextmanager
def collect_transaction_errors(db_name):
    try:
        yield
    except sqlite.OperationalError:
        # we should not be able to commit, so ignore this, we can't to anything about it, either
        pass
    else:
        logger.error("Was able to commit successfully on db %s, this should not happen" % db_name)

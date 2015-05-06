# coding=utf-8
import sqlite3 as sqlite
import logging
import time
import re

import databases
import network_params
import pydb
from pydb.documents import document_export_filter
import sqlitedb

logger = logging.getLogger('basedb')


class BaseDB(sqlitedb.SqliteDB):
    def __init__(self, db_file_path, schema_dir, init_sql_file, enable_db_sync):
        logger.info("Loading db from {}".format(db_file_path))

        sqlitedb.SqliteDB.__init__(self, db_file_path, schema_dir)

        try:
            logger.debug("Loading common schema")
            self._execute_sql_file('db-schema-common.sql')
            logger.debug("Loading specialized schema")
            self._execute_sql_file(init_sql_file)
            logger.debug("Done loading schemas")
        except sqlite.IntegrityError, e:  # error if already exists, \todo why is that so?
            logger.info("Before rollback due to %s" % repr(e))
            self.rollback()
        if not enable_db_sync:
            self.cur.execute("PRAGMA synchronous = OFF ")

    def get_base_statistics(self):
        authors = self.count_rows('authors', 'fidelity >=?', [network_params.Min_Relevant_Fidelity])
        tomes = self.count_rows('tomes', 'fidelity >=?', [network_params.Min_Relevant_Fidelity])
        files = self.count_rows('files', 'fidelity >=?', [network_params.Min_Relevant_Fidelity])

        stats = {"authors": authors,
                 "tomes": tomes,
                 "files": files}
        return stats

    def get_used_languages(self):
        return self.get_single_column("SELECT DISTINCT(principal_language) "
                                      "FROM tomes WHERE fidelity >= ?",
                                      [network_params.Min_Relevant_Fidelity])

    def get_tome_statistics(self):
        result = {}
        rows = self.cur.execute(
            "SELECT type, principal_language, count(*) FROM tomes WHERE fidelity >= ? "
            "GROUP BY type, principal_language",
            [network_params.Min_Relevant_Fidelity])
        for row in rows:
            tome_type, lang, count = row
            if lang not in result:
                result[lang] = {None: 0, pydb.TomeType.Fiction: 0, pydb.TomeType.NonFiction: 0}

            if tome_type not in result[lang]:
                logger.error("Invalid tome type '{}' found in database, skipping count".format(tome_type))
                continue
            result[lang][tome_type] = count
        return result

    def get_tome(self, tome_id):
        """ returns a tome by id or None if not found"""
        return self.get_single_object("SELECT * FROM tomes WHERE id=?", [tome_id])

    def get_tome_by_guid(self, guid):
        """ returns a tome by guid or None if not found
        """
        return self.get_single_object("SELECT * FROM tomes WHERE guid=?", [guid])

    def get_random_tomes(self, number_tomes):
        """ returns generator function for a specified number of tomes selected at random,
        less if no more are available """

        for row in self.cur.execute("SELECT * FROM tomes ORDER BY RANDOM() LIMIT ?", [number_tomes]):
            fields = {key: row[key] for key in row.keys()}
            yield fields

    def tome_id_to_guid(self, tome_id):
        return self.get_single_value("SELECT guid FROM tomes WHERE id=?", [tome_id])

    def get_all_tomes(self):
        """ returns generator function for all tome dicts """

        for row in self.cur.execute("SELECT * FROM tomes"):
            fields = {key: row[key] for key in row.keys()}
            yield fields

    def do_authors_match(self, authors_filter, tome_id):
        if not authors_filter:
            return True

        tome_author_ids = self.get_tome_author_ids(tome_id)
        for required_author_id in authors_filter:
            if required_author_id not in tome_author_ids:
                return False
        return True

    def find_tomes_by_title(self, title, principal_language, authors_filter=None, subtitle_filter_text=None):
        """ finds tomes by title
            authors_filter: list of author ids - if given, the tome must have at least these authors
        """

        result = self.get_list_of_objects("SELECT * FROM tomes WHERE title LIKE ? and principal_language=?",
                                          [title, principal_language])

        if subtitle_filter_text is not None:
            result = [tome for tome in result if (tome['subtitle'] or '').lower() == subtitle_filter_text.lower()]

        if authors_filter is not None:
            result = [tome for tome in result if self.do_authors_match(authors_filter, tome['id'])]
        return result

    def get_tomes_by_author(self, author_id):
        """ returns a list of tome dicts for all tomes by a certain author """
        return self.get_list_of_objects("SELECT tomes.*, tomes_authors.fidelity AS author_link_fidelity FROM tomes "
                                        "INNER JOIN tomes_authors ON tomes_authors.tome_id=tomes.id "
                                        "WHERE tomes_authors.author_id=?",
                                        [author_id])

    def get_all_tome_ids(self):
        return self.get_single_column("SELECT id FROM tomes")

    def get_all_tome_guids(self):
        return self.get_single_column("SELECT guid FROM tomes")

    def get_item_linked_to_tome_by_tome_id(self, table_name, tome_id):
        if not re.match("^[a-z_]+$", table_name):
            raise ValueError("Invalid table table {}".format(table_name))

        return self.get_single_object("SELECT * FROM " + table_name + " WHERE tome_id=?", [tome_id])

    def get_author_by_guid(self, guid):
        """ returns a author by guid or None if not found"""
        return self.get_single_object("SELECT * FROM authors WHERE guid=?", [guid])

    def get_author(self, author_id):
        """ returns a author by id or None if not found"""
        return self.get_single_object("SELECT * FROM authors WHERE id=?", [author_id])

    def find_authors(self, author_name):
        """ finds a author by name """

        result = []
        name_without_wildcards = author_name.replace('%', '').lower()

        for row in self.cur.execute("SELECT * FROM authors WHERE name LIKE ? ORDER BY name, date_of_birth, guid",
                                    [author_name]):
            fields = {key: row[key] for key in row.keys()}
            if fields['name'].lower() == name_without_wildcards:
                result.insert(0, fields)
            else:
                result.append(fields)

        return result

    def get_tome_author_ids(self, tome_id):
        """ returns a list of author ids for all authors linked to a tome, in order of priority """
        return self.get_single_column("SELECT author_id FROM tomes_authors WHERE tome_id=? ORDER BY author_order ASC",
                                      [tome_id])

    # this function is not according to the get_xxx_schema - it also gets data from the authors table
    def get_tome_authors(self, tome_id):
        """ returns a of author dicts for all authors linked to a tome, in order of priority """
        return self.get_list_of_objects("SELECT authors.*, tomes_authors.author_order AS author_order, "
                                        "tomes_authors.fidelity AS link_fidelity, "
                                        "tomes_authors.last_modification_date AS link_last_modification_date "
                                        "FROM authors "
                                        "INNER JOIN tomes_authors ON authors.id=tomes_authors.author_id "
                                        "WHERE tome_id=? ORDER BY author_order ASC", [tome_id])

    def get_tome_authors_with_guid_by_tome_guid(self, tome_guid):
        """ returns a list of tome author link info with author guid for all
        authors linked to a tome, in order of priority """
        return self.get_list_of_objects("SELECT authors.guid AS author_guid, tomes_authors.* "
                                        "FROM tomes_authors "
                                        "INNER JOIN authors ON authors.id=tomes_authors.author_id "
                                        "INNER JOIN tomes ON tomes.id=tomes_authors.tome_id "
                                        "WHERE tomes.guid=? ORDER BY author_order ASC", [tome_guid])

    def add_tome_author_link(self, local_db_tome_id, local_db_author_id, author_order, fidelity):
        self.cur.execute("INSERT OR IGNORE INTO tomes_authors "
                         "(tome_id, author_id, author_order, fidelity, last_modification_date) VALUES(?,?,?,?,?)",
                         (local_db_tome_id, local_db_author_id, author_order, fidelity, time.time()))

    def get_all_authors(self):
        """ returns all author dicts """
        return self.get_list_of_objects("SELECT * FROM authors")

    def get_all_author_ids(self):
        return self.get_single_column("SELECT id FROM authors")

    def get_all_author_guids(self):
        return self.get_single_column("SELECT guid FROM authors")

    def get_tome_author_entry(self, tome_id, author_id):
        """ returns the item for the tome <-> author connection, None if no link """
        return self.get_single_object("SELECT * FROM tomes_authors WHERE tome_id=? AND author_id=?",
                                      [tome_id, author_id])

    def get_tome_author_entry_by_guid(self, tome_guid, author_guid):
        """ returns the item for the tome <-> author connection, None if no link """

        tome = self.get_tome_by_guid(tome_guid)
        if tome is None:
            return None

        author = self.get_author_by_guid(author_guid)
        if author is None:
            return None

        return self.get_tome_author_entry(tome['id'], author['id'])

    def get_tome_file(self, tome_id, file_hash):
        """ returns a tome file link entry or None if not found"""
        return self.get_single_object("SELECT * FROM files WHERE tome_id=? AND hash=?", [tome_id, file_hash])

    def get_tome_files(self, tome_id, file_type=pydb.FileType.Content):
        """ returns a dictionary of file_fields for all files linked to the given tome """

        return self.get_list_of_objects("SELECT * FROM files "
                                        "WHERE tome_id=? AND file_type=? ORDER BY fidelity DESC, hash DESC",
                                        [tome_id, file_type])

    def get_tome_files_by_hash(self, file_hash):
        """ returns a list tome file links having the given file_hash """

        return self.get_list_of_objects("SELECT * FROM files "
                                        "WHERE hash=?", [file_hash])

    def get_tome_tags(self, tome_id):
        """ returns a dictionary of tag_fields for all tags linked to the given tome """

        return self.get_list_of_objects("SELECT * FROM tome_tags "
                                        "WHERE tome_id=? ORDER BY fidelity DESC, tag_value DESC", [tome_id])

    def get_tome_synopses(self, tome_id):
        """ returns a list containing dictionaries of synopsis_fields for all synopses linked to the given tome """

        return self.get_list_of_objects("SELECT * FROM synopses "
                                        "WHERE tome_id=? ORDER BY fidelity DESC", [tome_id])

    def get_author_fusion_sources(self, author_id):
        """ returns a list containing dictionaries of fusion info linked to the given author """

        return self.get_list_of_objects("SELECT * FROM author_fusion_sources "
                                        "WHERE author_id=? ORDER BY fidelity DESC, source_guid DESC", [author_id])

    def is_author_a_fusion_source(self, author_guid):
        """ return true if the given author_guid is an source for an active fusion
        """
        number_entries = self.count_rows("author_fusion_sources",
                                         "source_guid=? and fidelity >= ?",
                                         [author_guid, network_params.Min_Relevant_Fidelity])
        return number_entries > 0

    def get_author_fusion_target_guid(self, source_guid):
        """ returns the target guid if the given source_guid is an source for an active fusion
        """
        target_author_id = self.get_author_fusion_target_id(source_guid)
        if target_author_id is None:
            return None

        target_author = self.get_author(target_author_id)
        return target_author['guid']

    def get_author_fusion_target_id(self, source_guid):
        """ returns the target id if the given source_guid is an source for an active fusion
        """
        target_author_id = self.get_single_value("SELECT author_id FROM author_fusion_sources "
                                                 "WHERE source_guid=? and fidelity >= ?",
                                                 [source_guid, network_params.Min_Relevant_Fidelity])

        return target_author_id

    def replace_author_fusion_targets(self, old_author_id, new_author_id):
        self.cur.execute("UPDATE author_fusion_sources SET author_id=? WHERE author_id=?",
                         [new_author_id, old_author_id])

    def get_all_relevant_author_fusion_source_guids(self, author_id):
        """ returns a list of guids containing all source guids (recursively) of the given author
        """
        direct_children_guids = self.get_single_column("SELECT source_guid FROM author_fusion_sources "
                                                       "WHERE author_id=? AND fidelity >= ? ORDER BY source_guid DESC",
                                                       [author_id, network_params.Min_Relevant_Fidelity])

        result = []
        for child_guid in direct_children_guids:
            result.append(child_guid)
            item = self.get_author_by_guid(child_guid)
            if item:
                result += self.get_all_relevant_author_fusion_source_guids(item['id'])

        return result

    def get_all_relevant_author_fusion_target_guids(self, source_guid):
        """ returns a list of guids containing all target guids (recursively) of the given author
        """

        result = []

        target_guid = self.get_author_fusion_target_guid(source_guid)
        while target_guid:
            result.append(target_guid)
            target_guid = self.get_author_fusion_target_guid(target_guid)

        return result

    def get_author_fusion_sources_by_author_guid(self, author_guid):
        """ returns a list of author fusion entries associated to the author identified by author_guid """

        return self.get_list_of_objects("SELECT author_fusion_sources.* FROM author_fusion_sources "
                                        "INNER JOIN authors ON author_fusion_sources.author_id = authors.id "
                                        "WHERE authors.guid=? "
                                        "ORDER BY fidelity DESC, source_guid DESC", [author_guid])

    def get_tome_fusion_sources(self, tome_id):
        """ returns a list containing dictionaries of fusion info linked to the given tome """
        return self.get_list_of_objects("SELECT * FROM tome_fusion_sources "
                                        "WHERE tome_id=? ORDER BY fidelity DESC, source_guid DESC", [tome_id])

    def is_tome_a_fusion_source(self, tome_guid):
        """ return true if the given tome_guid is an source for an active tome fusion
        """
        count = self.count_rows("tome_fusion_sources ",
                                "source_guid=? and fidelity >= ?",
                                [tome_guid, network_params.Min_Relevant_Fidelity])
        return count > 0

    def get_tome_fusion_target_guid(self, source_tome_guid):
        """ returns the target guid if the given tome_guid is an source for an active fusion
        """
        target_tome_id = self.get_single_value("SELECT tome_id FROM tome_fusion_sources "
                                               "WHERE source_guid=? and fidelity >= ?",
                                               [source_tome_guid, network_params.Min_Relevant_Fidelity])
        if target_tome_id is None:
            return None

        logger.debug("Found target tome with id {}".format(target_tome_id))
        target_tome = self.get_tome(target_tome_id)
        if target_tome is None:
            raise RuntimeError(
                "Target tome ({}) for fusion of {} specified, but not in database - consistency error!"
                .format(target_tome_id, source_tome_guid))
        return target_tome['guid']

    def get_tome_fusion_target_id(self, source_tome_guid):
        """ returns the target id if the given tome_guid is an source for an active fusion
        """
        return self.get_single_value("SELECT tome_id FROM tome_fusion_sources "
                                     "WHERE source_guid=? and fidelity >= ?",
                                     [source_tome_guid, network_params.Min_Relevant_Fidelity])

    def replace_tome_fusion_targets(self, old_tome_id, new_tome_id):
        logger.debug("Replacing tome fusion source {} => {} ".format(old_tome_id, new_tome_id))
        self.cur.execute("UPDATE tome_fusion_sources SET tome_id=? WHERE tome_id=?", [new_tome_id, old_tome_id])

    def get_final_author_fusion_target_guid(self, source_author_guid):
        target_guid = self.get_author_fusion_target_guid(source_author_guid)
        if target_guid is None:
            return None

        next_target_guid = target_guid
        while next_target_guid is not None:
            target_guid = next_target_guid
            next_target_guid = self.get_author_fusion_target_guid(next_target_guid)
        return target_guid

    def get_all_relevant_tome_fusion_source_guids(self, tome_id):
        """ returns a list of guids containing all source guids (recursively) of the given tome
        """
        direct_children_guids = self.get_single_column("SELECT source_guid FROM tome_fusion_sources "
                                                       "WHERE tome_id=? AND fidelity >= ? ORDER BY source_guid DESC",
                                                       [tome_id, network_params.Min_Relevant_Fidelity])

        result = []
        for child_guid in direct_children_guids:
            result.append(child_guid)
            tome = self.get_tome_by_guid(child_guid)
            if tome:
                result += self.get_all_relevant_tome_fusion_source_guids(tome['id'])

        return result

    def get_all_relevant_tome_fusion_target_guids(self, source_guid):
        """ returns a list of guids containing all target guids (recursively) of the given tome
        """

        result = []

        target_guid = self.get_tome_fusion_target_guid(source_guid)
        while target_guid:
            result.append(target_guid)
            target_guid = self.get_tome_fusion_target_guid(target_guid)
        return result

    def get_tome_fusion_sources_by_tome_guid(self, tome_guid):
        """ returns a list of tome fusion entries associated to the tome identified by tome_guid """

        return self.get_list_of_objects("SELECT tome_fusion_sources.* FROM tome_fusion_sources "
                                        "INNER JOIN tomes ON tome_fusion_sources.tome_id = tomes.id "
                                        "WHERE tomes.guid=? ORDER BY fidelity DESC, source_guid DESC", [tome_guid])

    def get_tome_synopses_by_tome_guid(self, tome_guid):
        """ returns a list of tome files associated to the tome identified by tome_guid """

        return self.get_list_of_objects("SELECT synopses.* FROM synopses "
                                        "INNER JOIN tomes ON synopses.tome_id = tomes.id "
                                        "WHERE tomes.guid=? ORDER BY fidelity DESC", [tome_guid])

    def get_tome_files_by_tome_guid(self, tome_guid):
        """ returns a list of tome files associated to the tome identified by tome_guid """
        return self.get_list_of_objects("SELECT files.* FROM files "
                                        "INNER JOIN tomes ON files.tome_id=tomes.id WHERE tomes.guid=?",
                                        [tome_guid])

    def get_tome_tags_by_tome_guid(self, tome_guid):
        """ returns a list of tome files associated to the tome identified by tome_guid """

        return self.get_list_of_objects("SELECT tome_tags.* FROM tome_tags "
                                        "INNER JOIN tomes ON tome_tags.tome_id=tomes.id WHERE tomes.guid=?",
                                        [tome_guid])

    def _delete_tome_referrers(self, tome_id):
        self.cur.execute("DELETE FROM tomes_authors WHERE tome_id=?", [tome_id])
        self.cur.execute("DELETE FROM files WHERE tome_id=?", [tome_id])
        self.cur.execute("DELETE FROM tome_tags WHERE tome_id=?", [tome_id])
        self.cur.execute("DELETE FROM synopses WHERE tome_id=?", [tome_id])
        self.cur.execute("DELETE FROM tome_fusion_sources WHERE tome_id=?", [tome_id])

    def delete_tome(self, tome_id):
        """ removes a tome from the database, including all items referencing it
        """
        self._delete_tome_referrers(tome_id)
        self.cur.execute("DELETE FROM tomes WHERE id=?", [tome_id])

    def delete_tome_by_guid(self, guid):
        """ removes a tome from the database, including all items referencing it
        """
        tome = self.get_tome_by_guid(guid)
        if tome:
            self.delete_tome(tome['id'])

    def apply_tome_document(self, doc):
        """ applies a new tome document to the database
            note: currently this document deletes all stuff associated with the tome from the database and imports
            it again.
            In an optimisation step we could read the current stuff from the db and only write new stuff if required.
            see merge db for a way to do that.
            This also means that at the moment we have to trigger a merge db recalculation even if
            stuff might not have been changed at all - but mergedb will detect that
        """
        if 'prepared' not in doc:
            raise ValueError(u'Tome doc not prepared: {}'.format(doc))
        guid = doc['guid']

        logger.debug(u'Applying update for tome {} {}'.format(guid, doc))

        # check authors for existence to avoid inserting incomplete entries
        author_links = []
        for author_link_info in doc['authors']:
            author_guid = author_link_info['guid']
            author = self.get_author_by_guid(author_guid)
            if author is None:
                raise KeyError("No author with guid {} for tome {} found, skipping tome import ".format(author_guid,
                                                                                                        guid))
            author_links.append((author_link_info, author['id']))

        old_tome = self.get_tome_by_guid(guid)

        tome_data = {
            'guid': doc['guid'],
            'title': doc['title'],
            'subtitle': doc['subtitle'],
            'edition': doc['edition'],
            'principal_language': doc['principal_language'],
            'publication_year': doc['publication_year'],
            'fidelity': doc['fidelity'],
            'type': doc['type'],
            'last_modification_date': time.time()
        }

        if old_tome:
            logger.debug("Updating old tome %s to %s" % (guid, repr(tome_data)))
            self.update_object('tomes', {'guid': doc['guid']}, tome_data)
            tome_id = old_tome['id']
            self._delete_tome_referrers(tome_id)
        else:
            logger.debug("Creating a new tome %s for %s" % (guid, repr(tome_data)))
            tome_id = self.insert_object('tomes', tome_data)

        for author_link_info, author_id in author_links:
            l = author_link_info

            self.cur.execute(
                "INSERT INTO tomes_authors ( tome_id, author_id, author_order, fidelity, last_modification_date ) "
                "VALUES(?,?,?,?,?)",
                [tome_id, author_id, l['order'], l['fidelity'], time.time()])

        for file_info in doc['files']:
            f = file_info
            sha256_hash_of_zero_bytes = 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
            if f['hash'].lower() != sha256_hash_of_zero_bytes:
                databases.insert_tome_file(self.cur, tome_id, f)

        processed_tags = set()
        for tag_info in doc['tags']:
            t = tag_info

            if not t['tag_value'] in processed_tags:
                processed_tags.add(t['tag_value'])
                databases.insert_tome_tag(self.cur, tome_id, t)

        for s in doc['synopses']:
            databases.insert_synopsis(self.cur, tome_id, s)

        for s in doc['fusion_sources']:
            databases.insert_tome_fusion(self.cur, tome_id, s)

    def _delete_author_referrers(self, author_id, include_tome_links=False):
        self.cur.execute("DELETE FROM author_fusion_sources WHERE author_id=?", [author_id])

        if include_tome_links:
            self.cur.execute("DELETE FROM tomes_authors WHERE author_id=?", [author_id])

    def delete_author(self, author_id):
        """ removes a author from the database, including all items referencing it
        """
        self._delete_author_referrers(author_id, include_tome_links=True)
        self.cur.execute("DELETE FROM authors WHERE id=?", [author_id])

    def delete_author_by_guid(self, guid):
        """ removes an author from the database, including all items referencing it
        """
        author = self.get_author_by_guid(guid)
        if author:
            self.delete_author(author['id'])

    def apply_author_document(self, doc):
        """ applies a new author document to the database """
        guid = doc['guid']

        logger.debug("Applying update for author {}".format(guid))

        old_author = self.get_author_by_guid(guid)

        author_data = {
            'guid': doc['guid'],
            'name': doc['name'],
            'date_of_birth': doc['date_of_birth'],
            'date_of_death': doc['date_of_death'],
            'fidelity': doc['fidelity'],
            'last_modification_date': time.time()
        }

        if old_author:
            self.update_object('authors', {'guid': guid}, author_data)
            author_id = old_author['id']
            self._delete_author_referrers(author_id)
        else:
            logger.debug("Creating a new author %s for %s" % (guid, repr(author_data)))
            author_id = self.insert_object('authors', author_data)

        if 'fusion_sources' in doc:
            for s in doc['fusion_sources']:
                databases.insert_author_fusion(self.cur, author_id, s)

    def apply_file_hash_translation(self, source_hash, target_hash):
        """
        @returns a set of tome ids where translation was applied
        """
        result = self.get_single_column("SELECT tome_id FROM files WHERE hash=?", [source_hash])

        if result:
            # there might already be source and target hash linked to a file, so ignore errors and delete links to
            # source hash afterwards
            self.cur.execute("UPDATE OR IGNORE files SET hash=? WHERE hash=?", [target_hash, source_hash])
            self.cur.execute("DELETE FROM files WHERE hash=?", [source_hash])

        return set(result)

    def get_tome_document_by_guid(self, guid, ignore_fidelity_filter=False, include_author_detail=False, keep_id=False):
        """ returns a tome and all his dependencies as one dictionary without ids and modification dates"""

        tome = self.get_tome_by_guid(guid)
        if not tome or (tome['fidelity'] < network_params.Min_Relevant_Fidelity and not ignore_fidelity_filter):
            return {'guid': guid}

        tome_id = tome['id']
        if not keep_id:
            del tome['id']
        del tome['last_modification_date']

        authors = self.get_tome_authors(tome_id)
        tome['authors'] = [{'guid': author['guid'], 'order': author['author_order'],
                            'fidelity': author['link_fidelity']}
                           for author in authors]

        if include_author_detail:
            for author_result, author_db in zip(tome['authors'], authors):
                author_result['detail'] = author_db

        file_infos = self.get_tome_files(tome_id, file_type=pydb.FileType.Content) + \
                     self.get_tome_files(tome_id, file_type=pydb.FileType.Cover)
        tome['files'] = document_export_filter(file_infos, ignore_fidelity_filter)

        tag_infos = self.get_tome_tags(tome_id)
        tome['tags'] = document_export_filter(tag_infos, ignore_fidelity_filter)

        synopses = self.get_tome_synopses(tome_id)
        tome['synopses'] = document_export_filter(synopses, ignore_fidelity_filter)

        fusion_sources = self.get_tome_fusion_sources(tome_id)
        tome['fusion_sources'] = document_export_filter(fusion_sources, ignore_fidelity_filter)

        return tome

    def get_author_document_by_guid(self, author_guid, ignore_fidelity_filter=False, keep_id=False):
        """ returns an author and all his dependencies as one dictionary  without ids and modification dates """

        author = self.get_author_by_guid(author_guid)
        if not author or (author['fidelity'] < network_params.Min_Relevant_Fidelity and not ignore_fidelity_filter):
            return {'guid': author_guid}

        author_id = author['id']
        if not keep_id:
            del author['id']

        del author['last_modification_date']

        if 'name_key' in author:
            del author['name_key']

        fusion_sources = self.get_author_fusion_sources(author_id)
        author['fusion_sources'] = document_export_filter(fusion_sources, ignore_fidelity_filter)

        return author

    def check_for_consistency_problems(self):
        problems = {}

        def add_check(name, from_clause, where_clause, order_by_clause=None, params=()):
            items = self.get_rows(from_clause, where_clause, order_by_clause, params)
            problems[name] = items

        add_check('orphaned_tome_files',
                  from_clause="files LEFT JOIN tomes ON files.tome_id=tomes.id",
                  where_clause="tomes.id IS NULL")

        add_check('tome_links_without_authors',
                  from_clause="tomes_authors "
                              "LEFT JOIN authors ON tomes_authors.author_id = authors.id "
                              "LEFT JOIN tomes ON tomes_authors.tome_id=tomes.id",
                  where_clause="authors.id IS null")

        add_check('tome_links_without_tomes',
                  from_clause="tomes_authors "
                              "LEFT JOIN authors ON tomes_authors.author_id = authors.id "
                              "LEFT JOIN tomes ON tomes_authors.tome_id=tomes.id",
                  where_clause="tomes.id IS null")

        add_check('missing_tome_fusion_targets',
                  from_clause="tome_fusion_sources LEFT JOIN tomes ON tome_fusion_sources.tome_id = tomes.id",
                  where_clause="tomes.id IS NULL")

        add_check('missing_author_fusion_targets',
                  from_clause="author_fusion_sources LEFT JOIN authors ON author_fusion_sources.author_id = authors.id",
                  where_clause="authors.id IS NULL")

        return problems


def data_fields_equal(fields_a, fields_b):
    """ returns true if the data in fields_a equals data in fields_b
        note: special comparison rules apply (e.g. ignoring of modification dates)
    """
    logger.debug(u'Comparing {} to {}'.format(repr(fields_a), repr(fields_b)))

    keys_a = set(fields_a.keys())
    keys_b = set(fields_b.keys())

    ignore_keys = {'last_modification_date', 'id', 'tome_id', 'author_id', 'local_file_exists', 'name_key'}

    keys_a -= ignore_keys
    keys_b -= ignore_keys

    if keys_a != keys_b:
        logger.debug("Keys differ")
        return False

    for k in keys_a:
        if fields_a[k] != fields_b[k]:
            logger.debug("Values for '%s' differ: '%s' vs '%s'" % (k, fields_a[k], fields_b[k]))
            return False

    return True


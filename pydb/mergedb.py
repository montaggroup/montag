# coding=utf-8
import pydb.names
import network_params
import time
from collections import defaultdict, namedtuple
import logging
import databases
import pydb
import copy
import sqlitedb
import basedb
from basedb import data_fields_equal

logger = logging.getLogger('mergedb')


class MergeDB(basedb.BaseDB):
    def __init__(self, db_file_path, schema_dir, local_db, enable_db_sync):
        super(MergeDB, self).__init__(db_file_path, schema_dir, init_sql_file="db-schema-merge.sql",
                                      enable_db_sync=enable_db_sync)

        self.recalculation_needed = False
        self.local_db = local_db
        self.merge_sources = set()
        self._update_schema_if_necessary()
        logger.info("Merge DB initialized")

    def _update_schema_if_necessary(self):
        if self._get_schema_version() == 0:
            logger.info("Migrating MergeDB to V1, please wait")
            self._execute_sql_file('db-schema-update-merge_db_1.sql')
            logger.info("Migration complete")
            self._update_schema_if_necessary()
        if self._get_schema_version() == 1:
            logger.info("Migrating MergeDB to V2, please wait")
            self._execute_sql_file('db-schema-update-merge_db_2.sql')
            logger.info("Generating data for new fields")
            self._update_all_author_name_keys()
            logger.info("Migration complete")
            self._update_schema_if_necessary()
        if self._get_schema_version() == 2:
            logger.info("Migrating MergeDB to V3, please wait")
            self._execute_sql_file('db-schema-update-merge_db_3.sql')
            self.recalculation_needed = 'local'
            logger.info("Migration complete")
            self._update_schema_if_necessary()

    def recalculate_if_neccessary(self):
        if self.recalculation_needed == 'local':
            logger.info("Recalculating entries for which we have local ones")
            _recalculate_merge_db_entries_for_all_tomes_with_local_db_entries(self, self.local_db)

    def _update_all_author_name_keys(self):
        with sqlitedb.Transaction(self):
            authors = self.get_all_authors()
            for author in authors:
                name_key = pydb.names.calc_author_name_key(author['name'])
                author_data = {
                    'name_key': name_key,
                }
                self.update_object('authors', {'id': author['id']}, author_data)

    def delete_all(self):
        for table in (databases.data_tables + databases.local_tables):
            logger.debug(u"deleting contents of table {}".format(table))
            self.cur.execute("DELETE FROM {}".format(table))

    def _unipolar_opinion_sources(self):
        return self.merge_sources | {self.local_db}

    def _replace_tome(self, guid, new_tome_fields):
        old_tome = self.get_tome_by_guid(guid)

        logger.debug(u'new_tome_fields = {}'.format(repr(new_tome_fields)))
        if new_tome_fields is None:
            logger.info(u'Merge db delete request for tome {}'.format(guid))
            if old_tome:
                logger.debug(u'Deleting tome with guid %s from merge db'.format(guid))
                self.cur.execute('DELETE FROM tomes WHERE guid=?', [guid])
                self.update_document_modification_date_by_guid('tome', guid)

                # remove authors/tags/.. of this tome
                self._delete_tome_referrers(old_tome['id'])

            return

        doc = new_tome_fields
        tome_data = {
            'guid': doc['guid'],
            'title': doc['title'],
            'subtitle': doc['subtitle'],
            'edition': doc['edition'],
            'principal_language': doc['principal_language'],
            'publication_year': doc['publication_year'],
            'fidelity': doc['fidelity'],
            'last_modification_date': doc['last_modification_date'],
            'type': doc['type']
        }

        if not old_tome:
            logger.debug("Inserting tome with guid %s into merge db" % guid)
            self.insert_object('tomes', tome_data)
            self.update_document_modification_date_by_guid('tome', guid)
        else:
            if not data_fields_equal(old_tome, new_tome_fields):
                logger.debug("Updating tome with guid %s in merge db" % guid)
                self.update_object('tomes', {'guid': doc['guid']}, tome_data)
                self.update_document_modification_date_by_guid('tome', guid)
            else:
                logger.info("Tomes with guid %s do not differ (mergedb/merge result)" % guid)

    def _replace_author(self, guid, new_author_fields):
        old_author = self.get_author_by_guid(guid)

        if new_author_fields is None:
            logger.info("Merge db delete request for author {}".format(guid))
            if old_author:
                logger.info("Following db delete request for author %s" % guid)
                self.cur.execute("DELETE FROM authors WHERE guid=?", [guid])
                self.update_document_modification_date_by_guid('author', guid)

                # remove tomes/pseudonyms of this author 
                self._delete_author_referrers(old_author['id'], include_tome_links=True)
            return

        doc = new_author_fields
        name_key = pydb.names.calc_author_name_key(doc['name'])
        author_data = {
            'guid': doc['guid'],
            'name': doc['name'],
            'name_key': name_key,
            'date_of_birth': doc['date_of_birth'],
            'date_of_death': doc['date_of_death'],
            'fidelity': doc['fidelity'],
            'last_modification_date': doc['last_modification_date'],
        }

        if not old_author:
            self.insert_object('authors', author_data)
            self.update_document_modification_date_by_guid('author', guid)
        else:
            if not data_fields_equal(old_author, new_author_fields):
                self.update_object('authors', {'guid': guid}, author_data)
                self.update_document_modification_date_by_guid('author', guid)
            else:
                logger.debug("Authors do not differ")

    def _request_author_related_item_update(self, author_guid, item_name, item_key, get_item_by_guid_fct,
                                            replace_item_fct):
        logger.info(u'{} update requested for author guid {}'.format(item_name, author_guid))

        author = self.get_author_by_guid(author_guid)
        if not author:
            return
        author_id = author['id']

        all_guids_for_this_author = [author_guid]
        all_guids_for_this_author += self.get_all_relevant_author_fusion_source_guids(author_id)

        foreign_opinions = []
        local_opinions = []

        for author_data_guid in all_guids_for_this_author:
            for source in self.merge_sources:
                foreign_opinions += get_item_by_guid_fct(source, author_data_guid)
            local_opinions += get_item_by_guid_fct(self.local_db, author_data_guid)

        logger.debug("%s Opinions: %s" % (item_name, str(foreign_opinions)))
        # merge bipolar, there might be opinions opposing the item<->tome link
        new_items_dict = merge_items_bipolar(local_opinions, foreign_opinions, group_fun=lambda x: x[item_key])

        old_items = get_item_by_guid_fct(self, author_guid)
        old_items_dict = {x[item_key]: x for x in old_items}

        keys_to_add, keys_to_remove, keys_to_check = calculate_items_difference(old_items_dict, new_items_dict)

        for item_key in keys_to_add:
            replace_item_fct(author_id, None, new_items_dict[item_key])

        for item_key in keys_to_remove:
            replace_item_fct(author_id, old_items_dict[item_key], None)

        for item_key in keys_to_check:
            replace_item_fct(author_id, old_items_dict[item_key], new_items_dict[item_key])

    def _replace_tome_author_link(self, tome_id, old_item_data, new_item_data):
        """ either old_tome_author_link or new_tome_author_link (or both) have to be given
        item data must contain an author guid
        """

        table_name = "tomes_authors"
        item_name = "tome author link"

        def author_guid_to_id(author_guid):
            author = self.get_author_by_guid(author_guid)
            if author is None:
                return None
            return author['id']

        def enrich_with_author_id(item_data):
            item_data['author_id'] = author_guid_to_id(item_data['author_guid'])

        if old_item_data:
            enrich_with_author_id(old_item_data)

        if new_item_data:
            enrich_with_author_id(new_item_data)
            if new_item_data['author_id'] is None:
                new_item_data = None

        if old_item_data is None and new_item_data is None:
            return

        item_key = "author_id"

        self.replace_item_linked_to_tome(table_name, item_name, item_key, databases.insert_tome_author, tome_id,
                                         new_item_data, old_item_data)

    def replace_item_linked_to_tome(self, table_name, item_name, item_key, insert_item_fct, tome_id, new_item_data,
                                    old_item_data):
        tome = self.get_tome(tome_id)
        if new_item_data is None:
            self.cur.execute("DELETE FROM " + table_name + " WHERE tome_id=? AND " + item_key + "=?",
                             [tome_id, old_item_data[item_key]])
            logger.info("Updating mod date of tome %s due to %s delete: %s" % (tome_id, item_name, item_key))
            self.update_document_modification_date_by_guid('tome', tome['guid'])
            return

        need_update = False
        if not old_item_data:
            need_update = True
        else:
            if not data_fields_equal(old_item_data, new_item_data):
                need_update = True
            else:
                logger.info("%s information does not differ" % item_name)

        if need_update:
            insert_item_fct(self.cur, tome_id, new_item_data)
            self.update_document_modification_date_by_guid('tome', tome['guid'])

    def update_local_file_exists(self, file_hash):
        local_file_exists = 0
        if self.has_local_file(file_hash):
            local_file_exists = 1

        self.cur.execute("UPDATE files SET local_file_exists=? WHERE hash=?", [local_file_exists, file_hash])

    def _replace_tome_file(self, tome_id, old_item_data, new_item_data):
        """ either old_tome_file or new_tome_file (or both) have to be given 
        """

        table_name = "files"
        item_name = "file"
        item_key = "hash"

        self.replace_item_linked_to_tome(table_name, item_name, item_key, databases.insert_tome_file, tome_id,
                                         new_item_data, old_item_data)
        if new_item_data:
            self.update_local_file_exists(new_item_data['hash'])

    def _replace_tome_tag(self, tome_id, old_item_data, new_item_data):
        """ either old_tome_file or new_tome_file (or both) have to be given
        """

        table_name = "tome_tags"
        item_name = "tome tag"
        item_key = "tag_value"

        self.replace_item_linked_to_tome(table_name, item_name, item_key, databases.insert_tome_tag, tome_id,
                                         new_item_data, old_item_data)

    def _replace_tome_synopsis(self, tome_id, old_item_data, new_item_data):
        """ either old_item_data or new_item_data (or both) have to be given
        """

        table_name = "synopses"
        item_name = "synopsis"
        item_key = "guid"

        self.replace_item_linked_to_tome(table_name, item_name, item_key, databases.insert_synopsis, tome_id,
                                         new_item_data, old_item_data)

    def _replace_tome_fusion_source(self, tome_id, old_item_data, new_item_data):
        """ either old_item_data or new_item_data (or both) have to be given
            update of this item should be triggered by the caller afterwards
            downstream updates are also responsibility of the caller (e.g. by updating this item)
        """

        table_name = "tome_fusion_sources"
        item_name = "tome fusion source"
        item_key = "source_guid"

        self.replace_item_linked_to_tome(table_name, item_name, item_key, databases.insert_tome_fusion, tome_id,
                                         new_item_data, old_item_data)

        if old_item_data is not None:
            source_guid = old_item_data['source_guid']
        else:
            source_guid = new_item_data['source_guid']

        # update source, it may enter/leave merge db
        self.request_complete_tome_update(source_guid, include_fusion_source_update=False)

    def request_author_update(self, guid):
        """ updates the merged information for authors """

        pydb.assert_guid(guid)
        if self.is_author_a_fusion_source(guid):  # when we are a fusion source, this author will be deleted in merge db
            # if we are just in the process of being deleted, transfer all author_fusion sources to the new target
            our_author = self.get_author_by_guid(guid)
            if our_author is not None:  # we have not yet been deleted
                fusion_target_id = self.get_author_fusion_target_id(guid)
                if not fusion_target_id:
                    raise RuntimeError("Our author ({}) is a fusion source, but has no fusion target id".format(guid))
                self.replace_author_fusion_targets(our_author['id'], fusion_target_id)

            self._replace_author(guid, None)

            return

        author_data = [source.get_author_by_guid(guid) for source in self._unipolar_opinion_sources()]
        # authors: unipolar, as there is only one possible opinion per (author, peer)
        best_author = item_with_best_opinion_unipolar(author_data)

        if not best_author or best_author['fidelity'] < network_params.Min_Relevant_Fidelity:
            self._replace_author(guid, None)
        else:
            self._replace_author(guid, best_author)

    def request_author_fusion_source_update(self, author_guid):
        # do not update fusion info of fusion target: a) unnecessary because no data flow in this direction,
        # b) dangerous => loop possibility
        item_name = "author_fusion"
        item_key = "source_guid"
        get_item_by_guid = pydb.basedb.BaseDB.get_author_fusion_sources_by_author_guid
        replace_item = self._replace_author_fusion_source

        self._request_author_related_item_update(author_guid, item_name, item_key, get_item_by_guid, replace_item)

    def replace_item_linked_to_author(self, table_name, item_name, item_key, insert_item_fct, author_id, new_item_data,
                                      old_item_data):
        author = self.get_author(author_id)
        if new_item_data is None:
            self.cur.execute("DELETE FROM " + table_name + " WHERE author_id=? AND " + item_key + "=?",
                             [author_id, old_item_data[item_key]])
            logger.info("Updating mod date of tome %s due to %s delete: %s" % (author_id, item_name, item_key))
            self.update_document_modification_date_by_guid('author', author['guid'])
            return

        need_update = False
        if not old_item_data:
            need_update = True
        else:
            if not data_fields_equal(old_item_data, new_item_data):
                need_update = True
            else:
                logger.info("{} information does not differ".format(item_name))

        if need_update:
            insert_item_fct(self.cur, author_id, new_item_data)
            self.update_document_modification_date_by_guid('author', author['guid'])

    def _replace_author_fusion_source(self, author_id, old_item_data, new_item_data):
        """ either old_item_data or new_item_data (or both) have to be given
            update of this item should be triggered by the caller afterwards
            downstream updates are also responsibility of the caller (e.g. by updating this item)
        """

        table_name = "author_fusion_sources"
        item_name = "author fusion source"
        item_key = "source_guid"

        self.replace_item_linked_to_author(table_name, item_name, item_key, databases.insert_author_fusion, author_id,
                                           new_item_data, old_item_data)

        if old_item_data is not None:
            source_guid = old_item_data['source_guid']
        else:
            source_guid = new_item_data['source_guid']

        # determine all affected tomes
        affected_tomes = []

        # tomes attached to fusion source  \todo go back to source
        fusion_source = self.get_author_by_guid(source_guid)
        if fusion_source is not None:
            affected_tomes += self.get_tomes_by_author(fusion_source['id'])
        # tomes attached to this author
        affected_tomes += self.get_tomes_by_author(author_id)

        # update source, it may enter/leave merge db
        self.request_complete_author_update(source_guid, include_fusion_source_update=False)

        # update tome author links of affected tomes
        for tome in affected_tomes:
            self.request_tome_authors_update(tome['guid'])

    def request_complete_author_update(self, guid, include_fusion_source_update=True):
        """ convenience function calling all request_author_xxx_update functions one after the other """
        pydb.assert_guid(guid)

        if include_fusion_source_update:
            self.request_author_fusion_source_update(guid)

        self.request_author_update(guid)

    def request_tome_update(self, guid):
        """ updates the merged information for tomes """

        pydb.assert_guid(guid)
        if self.is_tome_a_fusion_source(guid):  # when we are a fusion source, this tome will be deleted in merge db

            # if we are just in the process of being deleted, transfer all tome_fusion sources to the new target
            our_tome = self.get_tome_by_guid(guid)
            if our_tome is not None:  # we have not yet been deleted
                our_tome_id = our_tome['id']

                fusion_target_id = self.get_tome_fusion_target_id(guid)
                if not fusion_target_id:
                    raise RuntimeError("Our tome ({}) is a fusion source, but has no fusion target id".format(guid))

                self.replace_tome_fusion_targets(our_tome_id, fusion_target_id)

            self._replace_tome(guid, None)
            return

        # do normal tome handling

        tome_data = [source.get_tome_by_guid(guid) for source in self._unipolar_opinion_sources()]
        # print "Tome data list from all sources for tome %s:\n%s" % (guid, tome_data)
        # tomes: unipolar, as there is only one possible opinion per (tome, peer)
        best_tome = item_with_best_opinion_unipolar(tome_data)

        if not best_tome or best_tome['fidelity'] < network_params.Min_Relevant_Fidelity:
            self._replace_tome(guid, None)
        else:
            self._replace_tome(guid, best_tome)

    def request_tome_file_update(self, tome_guid):
        fusion_target_guid = self.get_tome_fusion_target_guid(tome_guid)
        if fusion_target_guid:
            self.request_tome_file_update(fusion_target_guid)
        else:
            item_name = "file"
            item_key = "hash"
            get_item_by_guid = pydb.basedb.BaseDB.get_tome_files_by_tome_guid
            replace_item = self._replace_tome_file

            self._request_tome_related_item_update(tome_guid, item_name, item_key, get_item_by_guid, replace_item)

    def request_tome_tag_update(self, tome_guid):
        fusion_target_guid = self.get_tome_fusion_target_guid(tome_guid)
        if fusion_target_guid:
            self.request_tome_tag_update(fusion_target_guid)
        else:
            item_name = "tag"
            item_key = "tag_value"
            get_item_by_guid = pydb.basedb.BaseDB.get_tome_tags_by_tome_guid
            replace_item = self._replace_tome_tag

            self._request_tome_related_item_update(tome_guid, item_name, item_key, get_item_by_guid, replace_item)

    def request_tome_synopsis_update(self, tome_guid):
        fusion_target_guid = self.get_tome_fusion_target_guid(tome_guid)
        if fusion_target_guid:
            self.request_tome_synopsis_update(fusion_target_guid)
        else:
            item_name = "synopsis"
            item_key = "guid"
            get_item_by_guid = pydb.basedb.BaseDB.get_tome_synopses_by_tome_guid
            replace_item = self._replace_tome_synopsis

            self._request_tome_related_item_update(tome_guid, item_name, item_key, get_item_by_guid, replace_item)

    def request_tome_fusion_source_update(self, tome_guid):
        # do not update fusion info of fusion target: a) unnecessary because no data flow in this direction,
        # b) dangerous => loop possibility
        item_name = "tome_fusion"
        item_key = "source_guid"
        get_item_by_guid = pydb.basedb.BaseDB.get_tome_fusion_sources_by_tome_guid
        replace_item = self._replace_tome_fusion_source

        self._request_tome_related_item_update(tome_guid, item_name, item_key, get_item_by_guid, replace_item)

    def _request_tome_related_item_update(self, tome_guid, item_name, item_key, get_item_by_guid_fct, replace_item_fct):
        logger.info('{} update requested for guid {}'.format(item_name, tome_guid))

        tome = self.get_tome_by_guid(tome_guid)
        if not tome:
            return
        tome_id = tome['id']

        all_guids_for_this_tome = [tome_guid]
        all_guids_for_this_tome += self.get_all_relevant_tome_fusion_source_guids(tome_id)

        foreign_opinions = []
        local_opinions = []

        for tome_data_guid in all_guids_for_this_tome:
            for source in self.merge_sources:
                foreign_opinions += get_item_by_guid_fct(source, tome_data_guid)
            local_opinions += get_item_by_guid_fct(self.local_db, tome_data_guid)

        logger.debug(u'{} Opinions: {}'.format(item_name, foreign_opinions))
        # merge bipolar, there might be opinions opposing the item<->tome link
        new_items_dict = merge_items_bipolar(local_opinions, foreign_opinions, group_fun=lambda x: x[item_key])

        old_items = get_item_by_guid_fct(self, tome_guid)
        old_items_dict = {x[item_key]: x for x in old_items}

        keys_to_add, keys_to_remove, keys_to_check = calculate_items_difference(old_items_dict, new_items_dict)

        for item_key in keys_to_add:
            replace_item_fct(tome_id, None, new_items_dict[item_key])

        for item_key in keys_to_remove:
            replace_item_fct(tome_id, old_items_dict[item_key], None)

        for item_key in keys_to_check:
            replace_item_fct(tome_id, old_items_dict[item_key], new_items_dict[item_key])

    def request_tome_authors_update(self, tome_guid):
        fusion_target_guid = self.get_tome_fusion_target_guid(tome_guid)
        if fusion_target_guid:
            self.request_tome_authors_update(fusion_target_guid)
        else:
            item_name = "author"
            item_key = "author_guid"
            get_item_by_guid = self.get_tome_authors_with_guid_by_tome_guid_respecting_author_fusion
            replace_item = self._replace_tome_author_link

            self._request_tome_related_item_update(tome_guid, item_name, item_key, get_item_by_guid, replace_item)

    def get_tome_authors_with_guid_by_tome_guid_respecting_author_fusion(self, source, tome_guid):
        """ returns a list of tome author link info with author guid for all
        authors linked to a tome, in order of priority """
        authors = source.get_tome_authors_with_guid_by_tome_guid(tome_guid)

        for author in authors:
            guid = author['author_guid']
            target_guid = self.get_final_author_fusion_target_guid(guid)
            if target_guid is not None:
                author['author_guid'] = target_guid
        return authors

    def request_complete_tome_update(self, guid, include_fusion_source_update=True):
        """ convenience function calling all request_tome_xxx_update functions one after the other """
        if include_fusion_source_update:
            self.request_tome_fusion_source_update(guid)

        self.request_tome_update(guid)
        self.request_tome_file_update(guid)
        self.request_tome_tag_update(guid)
        self.request_tome_synopsis_update(guid)
        self.request_tome_authors_update(guid)

    def add_source(self, db):
        """ adds a db to the merge sources """
        self.merge_sources.add(db)

    def remove_source(self, db):
        """ removes a db from the merge sources """
        self.merge_sources.remove(db)

    def get_statistics(self):
        return self.get_base_statistics()

    def get_high_fidelity_tome_file_hashes_without_local_file(self, min_tome_fidelity, min_file_fidelity,
                                                              max_file_size_to_request_bytes, max_items):
        """ generator that yields tome file hashes having high fidelity values
        tome fidelity >= min_tome_fidelity, file fidelity >= min_file_fidelity) """

        for row in self.cur.execute(
                "SELECT files.hash FROM files "
                "INNER JOIN tomes ON tomes.id=files.tome_id "
                "WHERE files.fidelity > ? AND tomes.fidelity > ? AND files.local_file_exists = 0 "
                "AND files.size <= ? "
                "ORDER BY files.size ASC "
                "LIMIT ?",
                [min_file_fidelity, min_tome_fidelity, max_file_size_to_request_bytes, max_items]):
            yield row[0]

    def find_authors_with_same_name_key(self, author_name):
        """ finds a author by name key """
        key = pydb.names.calc_author_name_key(author_name)

        return self.get_list_of_objects("SELECT * FROM authors WHERE name_key=? ORDER BY name", [key])

    def document_modification_date_by_guid(self, doc_type, guid):
        table_name = doc_type + "_document_changes"
        result = self.get_single_value("SELECT last_modification_date FROM " + table_name + " WHERE document_guid=?",
                                       [guid])
        if result is None:
            return 0
        return result

    def update_document_modification_date_by_guid(self, doc_type, guid):
        table_name = doc_type + "_document_changes"
        current_mod_date = self.document_modification_date_by_guid(doc_type, guid)
        modification_date = time.time()
        if modification_date > current_mod_date:
            logger.debug(
                "Updating mod date for %s %s from %d to %d" % (doc_type, guid, current_mod_date, modification_date))
            self.cur.execute(
                "INSERT OR REPLACE INTO " + table_name + " (document_guid, last_modification_date) VALUES (?,?)",
                [guid, modification_date])

    def get_modified_document_guids(self, doc_type, max_count, min_modification_date, max_modification_date=None):
        """ returns a tuple containing a list of tuples ( doc_guid, last_mod_date) and max(last_mod_date) """
        table_name = doc_type + "_document_changes"
        result = []
        max_mod_date = -1

        if max_modification_date:
            rows = self.cur.execute(
                "SELECT document_guid, last_modification_date FROM " +
                table_name + " "
                "WHERE last_modification_date > ? "
                "AND last_modification_date <= ? ORDER BY last_modification_date ASC LIMIT ?",
                [min_modification_date, max_modification_date, max_count])
        else:
            rows = self.cur.execute(
                "SELECT document_guid, last_modification_date FROM " +
                table_name + " "
                "WHERE last_modification_date > ? ORDER BY last_modification_date ASC LIMIT ?",
                [min_modification_date, max_count])

        for row in rows:
            guid = row['document_guid']
            mod_date = row['last_modification_date']

            result.append((guid, mod_date))
            max_mod_date = row['last_modification_date']
        return result, max_mod_date

    def changed_documents_count(self, doc_type, min_modification_date):
        """ returns the number of changed documents of a given doc_type
        """
        table_name = doc_type + "_document_changes"

        row = self.cur.execute("SELECT count(document_guid) FROM " + table_name + " "
                                                                                  "WHERE last_modification_date > ? ",
                               [min_modification_date]).fetchone()
        return row[0]

    def get_number_of_modified_documents(self, doc_type):
        """ returns the number of changed documents of a given doc_type
        """
        table_name = doc_type + "_document_changes"

        row = self.cur.execute("SELECT count(document_guid) FROM " + table_name).fetchone()
        return row[0]

    def get_newest_modified_document_guids(self, doc_type, max_count, offset=0):
        """ returns a list of doc guids """
        table_name = doc_type + "_document_changes"
        result = []

        rows = self.cur.execute(
            "SELECT document_guid FROM " + table_name + " "
                                                        "ORDER BY last_modification_date DESC LIMIT ? OFFSET ?",
            [max_count, offset])

        for row in rows:
            guid = row['document_guid']

            result.append(guid)
        return result
        
    def insert_local_file(self, local_file):
        databases.insert_local_file(self.cur, local_file)
        self.update_local_file_exists(local_file['hash'])

    def remove_local_file(self, file_hash):
        self.cur.execute("DELETE FROM local_files WHERE hash=?", [file_hash])
        self.update_local_file_exists(file_hash)

    def get_local_file(self, file_hash):
        return self.get_single_object("SELECT * FROM local_files WHERE hash=?", [file_hash])

    def get_all_local_file_hashes(self):
        result = []
        rows = self.cur.execute("SELECT hash FROM local_files")

        for row in rows:
            result.append(row[0])
        return result

    def has_local_file(self, file_hash):
        rows = self.cur.execute("SELECT COUNT(hash) FROM local_files WHERE hash=?", [file_hash])
        row = rows.fetchone()
        return row[0] > 0

    def update_tomes_without_authors(self):
        rows = self.cur.execute("SELECT tomes.guid AS guid FROM tomes_authors "
                                "LEFT JOIN authors ON tomes_authors.author_id = authors.id "
                                "INNER JOIN tomes ON tomes_authors.tome_id=tomes.id "
                                "WHERE authors.id IS null")

        for row in rows:
            guid = row['guid']
            logger.debug("Updating tome authors for {}".format(guid))
            self.request_tome_authors_update(guid)

    def check_for_content_problems(self, filter_string=None):
        """ filter_string = None => show all
            filter_string = __list__ => show no items, just list the checks
            filter_string = something => only execute checks with "something" in name
        """

        problems = {}

        def add_check(name, from_clause, where_clause, order_by_clause=None, params=()):
            if filter_string is not None:
                if filter_string == "__list__":
                    problems[name] = []
                    return
                elif filter_string not in name:
                    return

            items = self.get_rows(from_clause, where_clause, order_by_clause, params)
            problems[name] = items

        add_check('authors_with_many_name_parts_and_fidelity_smaller_70',
                  from_clause='authors',
                  where_clause="(LENGTH(name) - LENGTH(REPLACE(name, ' ', ''))) > 5 AND fidelity < 70 AND fidelity >=?",
                  params=[network_params.Min_Relevant_Fidelity])

        add_check('authors_with_commas_in_name_and_fidelity_smaller_70',
                  from_clause='authors',
                  where_clause="name LIKE '%,%' AND name NOT LIKE '%, Jr.%' AND fidelity < 70 AND fidelity >=?",
                  params=[network_params.Min_Relevant_Fidelity])

        add_check('files_with_strange_extension',
                  from_clause="files INNER JOIN tomes ON tomes.id=files.tome_id",
                  where_clause="file_extension NOT IN "
                               "('epub', 'mobi', 'pdf', 'txt', 'pdb', 'jpg', 'html', 'lit', "
                               "'djvu','epub','rtf', 'azw3', 'azw4', 'png', 'gif', 'cbr') "
                               "AND files.fidelity >=?",
                  order_by_clause="files.hash",
                  params=[network_params.Min_Relevant_Fidelity])

        add_check('authors_with_identical_names',
                  from_clause="authors a1 INNER JOIN authors a2 ON a1.name=a2.name COLLATE NOCASE",
                  where_clause="a1.guid != a2.guid AND "
                               "( " 
                               " (a1.date_of_birth is NULL or a2.date_of_birth is NULL) "
                               " OR a1.date_of_birth=a2.date_of_birth "
                               ") AND "
                               "a1.fidelity >=? AND "
                               "a2.fidelity >=?",
                  order_by_clause="a1.name COLLATE NOCASE",
                  params=[network_params.Min_Relevant_Fidelity, network_params.Min_Relevant_Fidelity])

        add_check('authors_with_highly_similar_names',
                  from_clause="authors a1 INNER JOIN authors a2 ON a1.name_key=a2.name_key",
                  where_clause="a1.guid != a2.guid AND "
                               "( " 
                               " (a1.date_of_birth is NULL or a2.date_of_birth is NULL) "
                               " OR a1.date_of_birth=a2.date_of_birth "
                               ") AND "
                               "a1.fidelity >=? AND "
                               "a2.fidelity >=? AND "
                               "a1.name != a2.name COLLATE NOCASE",
                  order_by_clause="a1.name_key",
                  params=[network_params.Min_Relevant_Fidelity, network_params.Min_Relevant_Fidelity])

        add_check('authors_with_multiple_spaces_in_name',
                  from_clause='authors',
                  where_clause='name LIKE "%  %" AND fidelity >= ?',
                  params=[network_params.Min_Relevant_Fidelity])

        add_check('authors_with_only_one_name_part_and_fidelity_smaller_70',
                  from_clause='authors',
                  where_clause='name NOT LIKE "% %" AND fidelity <= ? AND fidelity >=?',
                  params=[70, network_params.Min_Relevant_Fidelity])

        add_check('files_linked_to_multiple_tomes',
                  from_clause="files f1 INNER JOIN tomes ON tomes.id=f1.tome_id",
                  where_clause="(SELECT count(*) FROM files f2 WHERE f1.hash=f2.hash AND f2.fidelity >= ?) > 1 "
                               "AND f1.fidelity >=?",
                  order_by_clause="f1.hash",
                  params=[network_params.Min_Relevant_Fidelity, network_params.Min_Relevant_Fidelity])

        add_check('authors_completely_uppercase_with_fidelity_smaller_70',
                  from_clause='authors',
                  where_clause='name=UPPER(name) AND name!=lower(name) AND fidelity < 70 AND fidelity >= ?',
                  params=[network_params.Min_Relevant_Fidelity])

        add_check('authors_having_whitespace_at_the_start_or_end',
                  from_clause='authors',
                  where_clause='name != TRIM(name)',
                  params=[])

        add_check('authors_completely_lowercase_with_fidelity_smaller_70',
                  from_clause='authors',
                  where_clause='name=lower(name) AND name!=upper(name) AND fidelity < 70 AND fidelity >= ?',
                  params=[network_params.Min_Relevant_Fidelity])

        add_check('tomes_completely_uppercase_with_fidelity_smaller_70',
                  from_clause='tomes',
                  where_clause='title=upper(title) AND title!=lower(title) AND fidelity < 70 AND fidelity >= ?',
                  params=[network_params.Min_Relevant_Fidelity])

        add_check('tomes_completely_lowercase_with_fidelity_smaller_70',
                  from_clause='tomes',
                  where_clause='title=lower(title) AND title!=upper(title) AND fidelity < 70 AND fidelity >= ?',
                  params=[network_params.Min_Relevant_Fidelity])

        add_check('tomes_with_invalid_type',
                  from_clause='tomes',
                  where_clause='type IS NOT NULL AND type NOT IN (1,2) AND fidelity >= ?',
                  params=[network_params.Min_Relevant_Fidelity])

        add_check('tomes_with_multiple_spaces_in_title_or_subtitle',
                  from_clause='tomes',
                  where_clause='title LIKE "%  %" or subtitle LIKE "%  %" AND fidelity >= ?',
                  params=[network_params.Min_Relevant_Fidelity])
            
        add_check('tomes_with_titles_ending_in_an_article_having_fidelity_smaller_70',
                  from_clause='tomes',
                  where_clause='(title LIKE "%, the" OR title LIKE "%, a" OR title LIKE "%, an") '
                               'AND fidelity >= ? AND fidelity < 70',
                  params=[network_params.Min_Relevant_Fidelity])

        add_check('tomes_with_titles_or_subtitle_containing_the_word_edition_having_fidelity_smaller_70',
                  from_clause='tomes',
                  where_clause='(title LIKE "% edition%" OR subtitle LIKE "% edition%") AND fidelity >= ? AND fidelity < 70',
                  params=[network_params.Min_Relevant_Fidelity])

        return problems


BipolarGroup = namedtuple('BipolarGroup', ['local_opinions', 'all_opinions'])


def merge_items_bipolar(local_opinions, foreign_opinions, group_fun):
    """ returns the merged version of items from multiple sources, grouped by group_fun.
    The result is a dictionary group_id => best item from group """

    def mkgroup():
        return BipolarGroup([], [])

    groups = defaultdict(mkgroup)
    for item in local_opinions:
        if item is None:
            continue
        logger.debug(u"Calling group on {}".format(str(item)))
        group_id = group_fun(item)
        groups[group_id].local_opinions.append(item)

    for item in foreign_opinions + local_opinions:
        if item is None:
            continue
        logger.debug(u"Calling group on {}".format(str(item)))
        group_id = group_fun(item)
        groups[group_id].all_opinions.append(item)

    group_winners = {}
    for group_id, group in groups.iteritems():
        group_winners[group_id] = item_with_best_opinion_bipolar(group)

    return group_winners


def extract_authoritative_local_opinion(local_opinions):
    if not local_opinions:
        return None

    if len(local_opinions) > 1:
        result = max(local_opinions, key=lambda o: o['last_modification_date'])
        logger.warning(u"Local opinion group has more than 1 entry: {} - using {}".format(local_opinions, result))
        return result

    return local_opinions[0]


def item_with_best_opinion_bipolar(bipolar_group):
    """ returns the best item of a group of items from multiple sources.
    all items here need to have the same 'message' in them """

    # remove none entries
    if not bipolar_group.all_opinions:
        return None

    min_item = min(bipolar_group.all_opinions, key=lambda x: x['fidelity'])
    min_fidelity = min(min_item['fidelity'], 0)

    max_item = max(bipolar_group.all_opinions, key=lambda x: x['fidelity'])
    max_fidelity = max(max_item['fidelity'], 0)

    result_item = copy.deepcopy(max_item)
    effective_fidelity = max_fidelity + min_fidelity
    result_item['fidelity'] = effective_fidelity

    # now overlay local
    local_item = extract_authoritative_local_opinion(bipolar_group.local_opinions)
    if local_item is not None:
        local_fidelity = local_item['fidelity']

        merge_fidelity = result_item['fidelity']
        if abs(local_fidelity) > abs(merge_fidelity) or local_fidelity * merge_fidelity < 0:
            result_item['fidelity'] = local_fidelity

    return result_item


def item_with_best_opinion_unipolar(items_of_one_group):
    """ returns the best item of a group of items from multiple sources,
    best being defined here by having the highest fidelity value """
    filtered_items = filter(lambda x: x, items_of_one_group)
    if not filtered_items:
        return None

    return max(filtered_items, key=lambda x: x['fidelity'])


def calculate_items_difference(old_items_dict, new_items_dict):
    old_keys = set(old_items_dict.keys())
    new_keys = set(new_items_dict.keys())

    keys_to_add = new_keys - old_keys
    keys_to_remove = old_keys - new_keys
    keys_to_check = new_keys & old_keys

    logger.debug("Keys to add: " + repr(keys_to_add))
    logger.debug("Keys to remove: " + repr(keys_to_remove))
    logger.debug("Keys to check: " + repr(keys_to_check))
    return keys_to_add, keys_to_remove, keys_to_check


def _recalculate_merge_db_entries_for_all_tomes_with_local_db_entries(merge_db, local_db):
    all_tomes = list(local_db.get_all_tomes())
    with sqlitedb.Transaction(merge_db):
        for tome in all_tomes:
            merge_db.request_complete_tome_update(tome['guid'], include_fusion_source_update=True)

import threading
import os
from pydb import mergedb
from pydb.network_params import relevant_items, relevant_links
from pydb import whooshindex
import json
import logging

# not a hard boundary, index server will try to keep update batches around this size
TARGET_INDEXING_BATCH_SIZE = 10000

logger = logging.getLogger('indexthread')


def build(db_dir, schema_dir):
    progress_file_name = os.path.join(db_dir, "whoosh_progress.txt")
    progress_file = ProgressFile(progress_file_name)
    return IndexThread(db_dir, schema_dir, progress_file)


class IndexThread(threading.Thread):
    def __init__(self, db_dir, schema_dir, progress_file):
        threading.Thread.__init__(self)
        self.progress_file = progress_file

        self.schema_dir = schema_dir
        self.db_dir = db_dir

        self.min_mod_date_authors, self.min_mod_date_tomes = self.progress_file.load_mod_dates()

        self.update_trigger = threading.Event()
        self.stop_trigger = threading.Event()

        self.merge_db = None
        self.whoosh_index = None
        self.update_count = 0

    def request_index_update(self):
        self.update_trigger.set()

    def request_stop(self):
        self.stop_trigger.set()
        self.update_trigger.set()

    def run(self):
        self.whoosh_index = whooshindex.build(self.db_dir)
        # @todo: can we split the merge db in one class with sources and one without?
        self.merge_db = mergedb.MergeDB(os.path.join(self.db_dir, "merge.db"), self.schema_dir,
                                        local_db=None, enable_db_sync=False)

        self._update_index()
        while True:
            self.update_trigger.wait()
            self.update_trigger.clear()

            if self.stop_trigger.is_set():
                break
            self._update_index()
        logger.info("Stopping thread")

    def _create_tome_change_list(self):
        all_updated = True

        update_batch_size = int(TARGET_INDEXING_BATCH_SIZE / 2)

        modified_author_guids, new_min_mod_date_authors = \
            self.merge_db.get_modified_document_guids("author", update_batch_size, self.min_mod_date_authors)
        logger.debug("{} authors have been modified".format(len(modified_author_guids)))

        if new_min_mod_date_authors > 0:
            self.min_mod_date_authors = new_min_mod_date_authors

        if len(modified_author_guids) >= update_batch_size:
            all_updated = False

        tome_guids_with_modified_authors = set()
        for author_guid, author_last_mod_date in modified_author_guids:
            author = self.merge_db.get_author_by_guid(author_guid)
            if author:
                author_id = author['id']
                affected_tomes = self.merge_db.get_tomes_by_author(author_id)
                tome_guids_with_modified_authors |= set([tome['guid'] for tome in affected_tomes])

        modified_tome_guids, new_min_mod_date_tomes = self.merge_db.get_modified_document_guids("tome",
                                                                                                update_batch_size,
                                                                                                self.min_mod_date_tomes)
        logger.debug("{} tomes have been modified".format(len(modified_tome_guids)))

        if new_min_mod_date_tomes > 0:
            self.min_mod_date_tomes = new_min_mod_date_tomes

        if len(modified_tome_guids) >= update_batch_size:
            all_updated = False
        tome_guids_to_update_in_index = tome_guids_with_modified_authors | set([x[0] for x in modified_tome_guids])

        deleted_tome_guids, tomes_with_authors_and_tags = _fetch_tomes(self.merge_db, tome_guids_to_update_in_index)

        return tomes_with_authors_and_tags, deleted_tome_guids, all_updated

    def _update_index(self):
        logger.debug("Updating Index")
        enriched_tomes, deleted_tome_guids, is_list_complete, = self._create_tome_change_list()

        logger.debug("Found {} changed tomes, {} deleted tomes up to {}".format(
            len(enriched_tomes), len(deleted_tome_guids), self.min_mod_date_tomes))

        if self.stop_trigger.is_set():
            return

        self.whoosh_index.add_enriched_tomes(enriched_tomes)
        self.whoosh_index.remove_tomes(deleted_tome_guids)
        if not is_list_complete:
            self.update_trigger.set()

        self.progress_file.persist_mod_dates(self.min_mod_date_tomes, self.min_mod_date_authors)

        self.update_count += len(enriched_tomes)
        logger.debug("{} items processed in total".format(self.update_count))


def _fetch_tomes(merge_db, tome_guids):
    tomes_with_authors_and_tags = []
    deleted_tome_guids = []

    for tome_guid in tome_guids:
        tome = merge_db.get_tome_by_guid(tome_guid)
        if tome is None:
            deleted_tome_guids.append(tome_guid)
            continue

        tome_id = tome['id']
        tome['authors'] = list(relevant_links(relevant_items(merge_db.get_tome_authors(tome_id))))
        tome['tags'] = list(relevant_items(merge_db.get_tome_tags(tome_id)))
        tomes_with_authors_and_tags.append(tome)

    return deleted_tome_guids, tomes_with_authors_and_tags


class ProgressFile(object):
    def __init__(self, progress_file_name):
        self.progress_file_name = progress_file_name

    def load_mod_dates(self):
        if os.path.exists(self.progress_file_name):
            wp = json.load(open(self.progress_file_name))
            min_mod_date_authors = wp['min_mod_date_authors']
            min_mod_date_tomes = wp['min_mod_date_tomes']

            return min_mod_date_authors, min_mod_date_tomes
        else:
            return 0, 0

    def persist_mod_dates(self, min_mod_date_tomes, min_mod_date_authors):
        wp = {'min_mod_date_tomes': min_mod_date_tomes,
              'min_mod_date_authors': min_mod_date_authors}
        json.dump(wp, open(self.progress_file_name, 'w'))


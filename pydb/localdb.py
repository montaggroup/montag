import pydb
import pydb.basedb
import time
import logging

logger = logging.getLogger('localdb')


class LocalDB(pydb.basedb.BaseDB):
    def __init__(self, db_file_path, schema_dir, enable_db_sync):
        pydb.basedb.BaseDB.__init__(self, db_file_path, schema_dir, init_sql_file="db-schema-local.sql",
                                    enable_db_sync=enable_db_sync)

        # print "Local DB inititalized"
        logger.info('Local DB inititalized')

    def add_tome(self, guid, title, principal_language, author_ids, fidelity, publication_year, edition,
                 subtitle, tome_type):
        """ adds a new tome, generating a guid. returns a tome_id
            is_fiction: None => unknown, True => fiction, False=>non_fiction
        """
        logger.debug("Before insert")
        self.cur.execute(
            "INSERT INTO tomes "
            "(guid, title, subtitle, edition, principal_language, publication_year, "
            "fidelity, last_modification_date, type) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            [guid, title, subtitle, edition, principal_language, publication_year, fidelity, time.time(), tome_type])

        logger.info("Last row id is %s", str(self.cur.lastrowid))
        tome_id = self.cur.lastrowid

        for index, author_id in enumerate(remove_duplicates_in_list(author_ids)):
            self.cur.execute(
                "INSERT INTO tomes_authors (tome_id, author_id, author_order, fidelity,last_modification_date) "
                "VALUES(?,?,?,?,?)",
                [tome_id, author_id, index, fidelity, time.time()])

        return tome_id

    def add_author(self, guid, name, fidelity, date_of_birth, date_of_death):
        """ adds a new author, generating a guid, returns the id of the author """
        self.cur.execute(
            "INSERT INTO authors (guid, name, date_of_birth, date_of_death, fidelity, last_modification_date) "
            "VALUES (?,?,?,?,?,?)",
            [guid, name, date_of_birth, date_of_death, fidelity, time.time()])
        return self.cur.lastrowid

    def add_synopsis_to_tome(self, guid, content, tome_id, fidelity):
        """ adds a new synopsis, does link it to tome """
        self.cur.execute(
            "INSERT INTO synopses (guid, content, tome_id, fidelity, last_modification_date) VALUES (?,?,?,?,?)",
            [guid, content, tome_id, fidelity, time.time()])
        return self.cur.lastrowid

    def add_tome_file_link(self, fidelity, file_extension, file_type, local_db_tome_id, local_file_hash,
                           local_file_size):
        pydb.assert_hash(local_file_hash)
        self.cur.execute(
            "INSERT OR IGNORE INTO files "
            "(tome_id,file_type, hash, size, file_extension, fidelity, last_modification_date) VALUES(?,?,?,?,?,?,?)",
            (local_db_tome_id, file_type, local_file_hash, local_file_size, file_extension, fidelity, time.time()))

    def remove_file_link(self, tome_id, file_hash):
        self.cur.execute("DELETE FROM files WHERE tome_id=? AND hash=?", [tome_id, file_hash])

    def get_file_links_to_missing_files(self):
        return self.get_list_of_objects("SELECT * FROM files LEFT JOIN local_files ON files.hash = local_files.hash "
                                        "WHERE local_files.hash IS NULL")

    def get_all_local_files(self):
        for row in self.cur.execute("SELECT * FROM local_files"):
            fields = {key: row[key] for key in row.keys()}
            yield fields

    def get_local_file_by_hash(self, file_hash):
        """ returns the local file object identified by hash or None if not found """
        return self.get_single_object("SELECT * FROM local_files WHERE hash=?", [file_hash])

    def does_local_file_exist(self, file_hash):
        result = self.cur.execute("SELECT hash FROM local_files WHERE hash=?", [file_hash]).fetchone()
        return bool(result)

    def add_local_file(self, file_hash, extension):
        self.cur.execute("INSERT OR IGNORE INTO local_files (last_modification_date, hash, file_extension) VALUES (?,?,?)",
                    (time.time(), file_hash, extension))
        last_row_id = self.cur.lastrowid
        if not last_row_id:  # insert was ignored
            local_file = self.get_local_file_by_hash(file_hash)
            return local_file['id']
            
        return last_row_id

    def remove_local_file(self, file_hash):
        self.cur.execute("DELETE FROM local_files WHERE hash=?", [file_hash])

    def add_tags_to_tome(self, tome_id, tags_values, fidelity):
        for tag_value in tags_values:
            if tag_value == "" or tag_value is None:
                raise ValueError("Invalid tag value: '%s'" % tag_value)

            self.cur.execute("INSERT OR IGNORE INTO tome_tags (tome_id, tag_value, fidelity, last_modification_date) "
                        "VALUES(?,?,?,?)",
                        (tome_id, tag_value, fidelity, time.time()))

            # stripping metadata from a file might change its hash. if we request file xx from a remote peer,

    # we might end up having a hash yy after stripping.
    #  This would lead to two problems:
    #  1. We will request the file xx again as we don't have it in our repo.
    #  2. File yy will not be linked to any tome.
    #  So we have to record that yy and xx are actually the same file. We will do this by using a translation table.
    #  We look at the file checksum before and after stripping (when expecting a certain file hash).
    #  If they differ, we add a translation xx => yy into merge db.
    #  We also replace all occurrences of the xx file hash in our foreign and local databases by yy - effectively
    #  removing all notions of xx from our system.
    #  When trying to request file yy we should also try to request xx. """

    def translate_file_hash(self, source_hash):
        """ finds the replacement hash for a given file hash
        returns the same hash if no translation available
        """

        rows = self.cur.execute("SELECT target_hash FROM file_hash_aliases WHERE source_hash=?", [source_hash])
        for row in rows:
            return row['target_hash']

        return source_hash

    def add_file_hash_translation(self, source_hash, target_hash):
        """ adds a source => target hash translation
        """

        self.cur.execute("INSERT OR REPLACE INTO file_hash_aliases (source_hash, target_hash) VALUES(?,?)",
                         [source_hash, target_hash])
        self.cur.execute("UPDATE file_hash_aliases SET target_hash=? WHERE target_hash=?", [target_hash, source_hash])

    def get_all_file_hash_translation_sources(self, target_hash):
        """ returns a list of all hashes that translate to target_hash (including target_hash) """

        result = [target_hash]
        result += self.get_single_column("SELECT source_hash FROM file_hash_aliases WHERE target_hash=?", [target_hash])
        return result

    def get_statistics(self):
        stats = self.get_base_statistics()
        stats['local_files'] = self.get_single_value("SELECT count (*) FROM local_files")
        return stats


def remove_duplicates_in_list(a_list):
    result = []
    seen = set()

    for el in a_list:
        if el not in seen:
            seen.add(el)
            result.append(el)

    return result
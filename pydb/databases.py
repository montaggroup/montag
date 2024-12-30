import time

data_tables = ["tome_types", "tomes", "tome_tags", "synopses", "files", "authors", "pseudonyms",
               "tomes_authors", "tome_fusion_sources", "author_fusion_sources"]

local_tables = ["local_files"]

tables_with_tome_link = ["files", "tome_tags", "synopses", "tome_fusion_sources"]


def insert_tome_file(con, tome_id, item_data):
    f = item_data
    con.execute(
        "INSERT OR REPLACE INTO files "
        "(tome_id, file_type, hash,  size, file_extension, fidelity, last_modification_date) "
        "VALUES(?,?,?,?,?,?,?)",
        (tome_id, f['file_type'], f['hash'], f['size'], f['file_extension'], f['fidelity'], time.time()))


def insert_tome_tag(con, tome_id, item_data):
    t = item_data
    con.execute(
        "INSERT OR REPLACE INTO tome_tags "
        "(tome_id, tag_value, fidelity, last_modification_date) "
        "VALUES(?,?,?,?)",
        (tome_id, t['tag_value'], t['fidelity'], time.time()))


def insert_synopsis(con, tome_id, item_data):
    t = item_data
    con.execute(
        "INSERT OR REPLACE INTO synopses "
        "(tome_id, guid, content, fidelity, last_modification_date) "
        "VALUES(?,?,?,?,?)",
        (tome_id, t['guid'], t['content'], t['fidelity'], time.time()))


def insert_tome_fusion(con, tome_id, item_data):
    t = item_data
    con.execute(
        "INSERT OR REPLACE INTO tome_fusion_sources "
        "(source_guid, tome_id, fidelity, last_modification_date) "
        "VALUES(?,?,?,?)",
        (t['source_guid'], tome_id, t['fidelity'], time.time()))


def insert_author_fusion(con, author_id, item_data):
    t = item_data
    con.execute(
        "INSERT OR REPLACE INTO author_fusion_sources "
        "(source_guid, author_id, fidelity, last_modification_date) "
        "VALUES(?,?,?,?)",
        (t['source_guid'], author_id, t['fidelity'], time.time()))


def insert_tome_author(con, tome_id, item_data):
    t = item_data

    con.execute(
        "INSERT OR REPLACE INTO tomes_authors "
        "( tome_id, author_id, author_order, fidelity, last_modification_date ) VALUES(?,?,?,?,?)",
        [tome_id, t['author_id'], t['author_order'], t['fidelity'], time.time()])


def insert_local_file(con, local_file):
    con.execute("INSERT OR IGNORE INTO local_files (last_modification_date, hash, file_extension) VALUES (?,?,?)",
                (time.time(), local_file['hash'], local_file['file_extension']))

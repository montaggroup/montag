import logging

import pydb.localdb
import pydb.friendsdb
import pydb.mergedb
import pydb.foreigndb
import pydb.maindb

import mock

logger = logging.getLogger('testing.helpers')

def build_main_db_memory_only(schema_path):
    """ builds a database with all subdatabases in memory """
    local_db = pydb.localdb.LocalDB(":memory:", schema_path, enable_db_sync=False)
    merge_db = pydb.mergedb.MergeDB(":memory:", schema_path, local_db=local_db, enable_db_sync=False)
    merge_db.add_source(local_db)
    friends_db = pydb.friendsdb.FriendsDB(":memory:", schema_path)
    index_server = mock.MagicMock()

    def build_foreign_db(friend_id):
        db = pydb.foreigndb.ForeignDB(":memory:", schema_path, friend_id, enable_db_sync=False)
        return db

    db = pydb.maindb.MainDB(local_db, friends_db, merge_db, build_foreign_db, index_server)

    logger.info("DBs initialized")
    return db
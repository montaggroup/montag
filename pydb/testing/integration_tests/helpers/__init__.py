import logging

import mock

import pydb.databases.localdb
import pydb.databases.friendsdb
import pydb.databases.mergedb
import pydb.databases.foreigndb
import pydb.databases.maindb

logger = logging.getLogger('testing.helpers')

def build_main_db_memory_only(schema_dir):
    """ builds a database with all subdatabases in memory """
    local_db = pydb.databases.localdb.LocalDB(":memory:", schema_dir, enable_db_sync=False)
    merge_db = pydb.databases.mergedb.MergeDB(":memory:", schema_dir, local_db=local_db, enable_db_sync=False)
    merge_db.add_source(local_db)
    friends_db = pydb.databases.friendsdb.FriendsDB(":memory:", schema_dir)
    index_server = mock.MagicMock()

    def build_foreign_db(friend_id):
        db = pydb.databases.foreigndb.ForeignDB(":memory:", schema_dir, friend_id, enable_db_sync=False)
        return db

    db = pydb.databases.maindb.MainDB(local_db, friends_db, merge_db, build_foreign_db, index_server)

    logger.info("DBs initialized")
    return db
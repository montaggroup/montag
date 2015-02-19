import pydb.basedb
import logging

logger = logging.getLogger('foreigndb')


class ForeignDB(pydb.basedb.BaseDB):
    def __init__(self, db_file_path, schema_dir, friend_id, enable_db_sync):
    
        pydb.basedb.BaseDB.__init__(self, db_file_path, schema_dir,
                                    init_sql_file="db-schema-foreign.sql", enable_db_sync=enable_db_sync)
        logger.info("Foreign DB for friend {} initialized".format(friend_id))

    def set_last_query_dates(self, query_date_authors, query_date_tomes):

        self.con.execute("UPDATE update_info SET last_query_date_authors=?, last_query_date_tomes=? "
                         "WHERE id=0", [query_date_authors, query_date_tomes])

    def get_last_query_dates(self):
        row = self.con.execute("SELECT last_query_date_authors, last_query_date_tomes FROM update_info").fetchone()
        return row['last_query_date_authors'], row['last_query_date_tomes']

import sqlite3 as sqlite
import logging
import os
import traceback

SqliteWriteLockTimeOutSeconds = 120

logger = logging.getLogger('sqlitedb')


class SqliteDB(object):
    def __init__(self, db_file_path, schema_dir):
        self.con = sqlite.connect(db_file_path, timeout=SqliteWriteLockTimeOutSeconds)
        self.con.isolation_level = None
        self.con.row_factory = sqlite.Row
        self.schema_dir = schema_dir
        self.cur = self.con.cursor()

        self.in_transaction = False

    def _set_schema_version(self, schema_version):
        self.con.execute("PRAGMA user_version=" + str(int(schema_version)))

    def _get_schema_version(self):
        for row in self.con.execute("PRAGMA user_version"):
            return row[0]

    def _execute_sql_file(self, file_name):
        with open(os.path.join(self.schema_dir, file_name), 'r') as f:
            script = f.read()
            self.con.executescript(script)

    def begin(self):
        self.con.execute("BEGIN")
        self.in_transaction = True

    def commit(self):
        self.con.execute("COMMIT")
        self.in_transaction = False

    def rollback(self):
        self.con.execute("ROLLBACK")
        self.in_transaction = False

    def count_rows(self, from_clause, where_clause="1", params=()):
        for row in self.con.execute("SELECT COUNT(*) AS count FROM " + from_clause + " WHERE " + where_clause, params):
            fields = {key: row[key] for key in row.keys()}
            return fields['count']

    def get_rows(self, from_clause, where_clause="1", order_by_clause=None, params=()):
        result = []

        query = "SELECT * FROM " + from_clause + " WHERE " + where_clause
        if order_by_clause is not None:
            query += " ORDER BY " + order_by_clause

        for row in self.con.execute(query, params):
            fields = {key: row[key] for key in row.keys()}
            result.append(fields)
        return result


class Transaction():
    def __init__(self, db):
        self.db = db
        self.active = True

    def __enter__(self):
        if self.db.in_transaction:
            self.active = False
        else:
            self.db.begin()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.active:
            if exc_type is None:
                self.db.commit()
            else:
                logger.info("Caught an exception {} {}, rolling back".format(exc_type, exc_val))
                traceback.print_tb(exc_tb)
                self.db.rollback()
                return False
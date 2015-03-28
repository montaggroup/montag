import sqlite3 as sqlite
import logging
import os
import traceback

SqliteWriteLockTimeOutSeconds = 120

logger = logging.getLogger('sqlitedb')


class SqliteDB(object):
    def __init__(self, db_file_path, schema_dir):
        con = sqlite.connect(db_file_path, timeout=SqliteWriteLockTimeOutSeconds)
        con.isolation_level = None
        con.row_factory = sqlite.Row
        self.schema_dir = schema_dir
        self.cur = con.cursor()

        self.in_transaction = False

    def _set_schema_version(self, schema_version):
        self.cur.execute("PRAGMA user_version=" + str(int(schema_version)))

    def _get_schema_version(self):
        for row in self.cur.execute("PRAGMA user_version"):
            return row[0]

    def _execute_sql_file(self, file_name):
        with open(os.path.join(self.schema_dir, file_name), 'r') as f:
            script = f.read()
            self.cur.executescript(script)

    def begin(self):
        self.cur.execute("BEGIN")
        self.in_transaction = True

    def commit(self):
        self.cur.execute("COMMIT")
        self.in_transaction = False

    def rollback(self):
        self.cur.execute("ROLLBACK")
        self.in_transaction = False

    def count_rows(self, from_clause, where_clause="1", params=()):
        for row in self.cur.execute(u"SELECT COUNT(*) AS count FROM " + from_clause + " WHERE " + where_clause, params):
            fields = {key: row[key] for key in row.keys()}
            return fields['count']

    def get_rows(self, from_clause, where_clause="1", order_by_clause=None, params=()):
        result = []

        query = u"SELECT * FROM " + from_clause + " WHERE " + where_clause
        if order_by_clause is not None:
            query += " ORDER BY " + order_by_clause

        for row in self.cur.execute(query, params):
            fields = {key: row[key] for key in row.keys()}
            result.append(fields)
        return result

    def get_single_column(self, query, params=()):
        result = []
        for row in self.cur.execute(query, params):
            result.append(row[0])
        return result

    def get_single_object(self, query, params=()):
        row = self.cur.execute(query, params).fetchone()
        if row is not None:
            return {key: row[key] for key in row.keys()}

    def get_list_of_objects(self, query, params=()):
        result = []
        for row in self.cur.execute(query, params):
            fields = {key: row[key] for key in row.keys()}
            result.append(fields)
        return result

    def get_single_value(self, query, params=()):
        row = self.cur.execute(query, params).fetchone()
        if row is not None:
            return row[0]

    def update_object(self, table_name, filter_dict, object_fields):
        assignments = [u'{} = ?'.format(field_name) for field_name in object_fields.iterkeys()]
        set_string = ', '.join(assignments)

        filter_conditions = [u'{} = ?'.format(field_name) for field_name in filter_dict.iterkeys()]
        filter_string = " AND ".join(filter_conditions)

        parameters = object_fields.values() + filter_dict.values()

        query = u'UPDATE {} SET {} WHERE {}'.format(table_name, set_string, filter_string)
        logger.debug(u'Update query is {} {}'.format(query, repr(parameters)))
        self.cur.execute(query, parameters)

    def insert_object(self, table_name, object_fields):
        field_string = ', '.join(object_fields.iterkeys())
        question_marks = ', '.join('?' * len(object_fields))

        value_list = object_fields.values()

        query = u'INSERT INTO {} ({}) VALUES ({}) '.format(table_name, field_string, question_marks)
        logger.debug(u'Insert query is ' + query + repr(value_list))
        self.cur.execute(query, value_list)

        return self.cur.lastrowid


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
                logger.info(u'Caught an exception {} {}, rolling back'.format(exc_type, exc_val))
                traceback.print_tb(exc_tb)
                self.db.rollback()
                return False
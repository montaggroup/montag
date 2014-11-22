import sqlite3 as sqlite
import os
import logging
import json
import sqlitedb

logger = logging.getLogger('friendsdb')


class FriendsDB(sqlitedb.SqliteDB):
    def __init__(self, db_file_path, schema_dir):

        sqlitedb.SqliteDB.__init__(self, db_file_path, schema_dir)

        try:
            logger.debug("Loading schema")
            self._execute_sql_file("db-schema-friends.sql")
            logger.debug("Done loading schemas")
        except sqlite.IntegrityError, e:  # error if already exists, \todo why is that so?
            logger.info("Before rollback due to %s" % repr(e))
            self.con.rollback()
            pass

        self._update_schema_if_necessary()
        logger.info("Friends DB initialized")

    def _update_schema_if_necessary(self):
        if self._get_schema_version() == 0:
            logger.info("Migrating FriendsDB to V1, please wait")
            self._execute_sql_file('db-schema-update-friends_db_1.sql')
            logger.info("Migration complete")
            self._update_schema_if_necessary()

    def add_friend(self, name):
        cur = self.con.cursor()
        cur.execute("INSERT INTO friends (name) VALUES(?)", [name])

        logger.info("Last row id is %s", str(cur.lastrowid))
        return cur.lastrowid

    def remove_friend(self, friend_id):
        self.con.execute("DELETE FROM friends WHERE ID=?", [friend_id])

    def get_friends(self):
        """ returns a list of friend dictionary """
        result = []
        for row in self.con.execute("SELECT * FROM friends"):
            fields = {key: row[key] for key in row.keys()}
            if 'comm_data' in fields:
                del fields['comm_data']
            result.append(fields)

        return result

    def get_friend_by_name(self, name):
        """ returns the dictionary of the friend given by name """
        for row in self.con.execute("SELECT * FROM friends WHERE name=?", [name]):
            fields = {key: row[key] for key in row.keys()}
            if 'comm_data' in fields:
                del fields['comm_data']
            return fields
        return None

    def get_friend(self, friend_id):
        """ returns the dictionary of the friend """
        for row in self.con.execute("SELECT * FROM friends WHERE id=?", [friend_id]):
            fields = {key: row[key] for key in row.keys()}
            if 'comm_data' in fields:
                del fields['comm_data']
            return fields
        return None

    def set_comm_data_string(self, friend_id, comm_data_string):
        # print "UPDATE friends SET comm_data=? WHERE id=?", [comm_data_string, friend_id]
        self.con.execute("UPDATE friends SET comm_data=? WHERE id=?", [comm_data_string, friend_id])

    def get_comm_data_string(self, friend_id):
        for row in self.con.execute("SELECT comm_data FROM friends WHERE id=?", [friend_id]):
            return row['comm_data']

    def set_name(self, friend_id, name):
        print "UPDATE friends SET name=? WHERE id=?", [name, friend_id]
        self.con.execute("UPDATE friends SET name=? WHERE id=?", [name, friend_id])

    def set_can_connect_to(self, friend_id, can_connect_to):
        self.con.execute("UPDATE friends SET can_connect_to=? WHERE id=?", [can_connect_to, friend_id])

    def is_locking_active(self):
        for row in self.con.execute("SELECT is_locked FROM format_info"):
            if row['is_locked'] == 1:
                return True
            return False
        return False

    def set_locking_active(self, locked, salt, iteration_count, encrypted_canary):
        self.con.execute(u"INSERT OR REPLACE INTO format_info "
                         u"(is_locked, salt, iteration_count, encrypted_canary, id) "
                         u"VALUES(?, ?, ?, ?, 1)",
                         [1 if locked else 0, buffer(salt), iteration_count, buffer(encrypted_canary)])

    def get_locking_info(self):
        for row in self.con.execute("SELECT * FROM format_info"):
            fields = {key: row[key] for key in row.keys()}
            return fields


def expand_comm_data(friend):
    """ does the modification inplace
    """
    if 'comm_data' in friend and friend['comm_data']:
        friend['comm_data'] = json.loads(friend['comm_data'])
    else:
        friend['comm_data'] = {}
    return friend


def clear_comm_data_secret(friend):
    """ replaces the secret to avoid leakage - does the modification inplace
    """

    if 'comm_data' in friend:
        cd = friend['comm_data']
        if 'secret' in cd:
            cd['secret'] = "__KEEP__"
    return friend

import unittest

import pydb.friendsdb
import pydb.testing.unittests


class test_delete_friends(unittest.TestCase):

    def setUp(self):
        self.friends_db = pydb.friendsdb.FriendsDB(":memory:", pydb.testing.guess_schema_dir())

    def test_get_non_existing_by_name(self):
        f = self.friends_db.get_friend_by_name("no friend")
        self.assertIsNone(f)

    def test_add_one(self):
        self.friends_db.add_friend("a friend")
        f = self.friends_db.get_friend_by_name("a friend")
        self.assertIsNotNone(f)
        self.assertEquals(f['name'], 'a friend')

    def test_add_returns_friend_id(self):
        friend_id = self.friends_db.add_friend("a friend")
        f = self.friends_db.get_friend(friend_id)
        self.assertIsNotNone(f)
        self.assertEquals(f['name'], 'a friend')

    def test_remove_one(self):
        friend_id = self.friends_db.add_friend("a friend")
        self.friends_db.remove_friend(friend_id)
        f = self.friends_db.get_friend(friend_id)
        self.assertIsNone(f)


class test_can_connect_to(unittest.TestCase):
    def setUp(self):
        self.friends_db = pydb.friendsdb.FriendsDB(":memory:", pydb.testing.guess_schema_dir())
        self.friend_id = friend_id = self.friends_db.add_friend("a friend")

    def test_setup(self):
        pass

    def test_get_can_connect_to_is_true_by_default(self):
        f = self.friends_db.get_friend(friend_id=self.friend_id)
        self.assertTrue(f['can_connect_to'])

    def test_get_can_connect_to_after_set_to_true(self):
        self.friends_db.set_can_connect_to(self.friend_id, True)
        f = self.friends_db.get_friend(friend_id=self.friend_id)
        self.assertTrue(f['can_connect_to'])

    def test_get_can_connect_to_after_set_to_false(self):
        self.friends_db.set_can_connect_to(self.friend_id, False)
        f = self.friends_db.get_friend(friend_id=self.friend_id)
        self.assertFalse(f['can_connect_to'])

if __name__ == '__main__':
    unittest.main()

# -*- coding: utf-8 -*-
import unittest

import pydb.commdatastore as commdatastore
import pydb.testing.unittests


class TestCommDataActivateLocking(unittest.TestCase):
    def setUp(self):
        self.cds = commdatastore.CommDataStore(":memory:", pydb.testing.guess_schema_dir())
        self.passphrase = "hello"
        commdatastore.default_iteration_count = 10

    def test_empty(self):
        pass

    def test_inactive_default(self):
        self.assertFalse(self.cds.is_locking_active())

    def test_activate_locking_once(self):
        self.cds.activate_locking(self.passphrase)
        self.assertTrue(self.cds.is_locking_active())
        self.assertTrue(self.cds.is_locked())

    def test_activate_locking_twice(self):
        self.cds.activate_locking(self.passphrase)
        self.assertRaises(OverflowError, self.cds.activate_locking, self.passphrase)

    def test_activate_locking_changes_comm_data(self):
        self.a_friend_id = self.cds._friends_db.add_friend('a_friend')

        old_comm_data_string = '{"secret": "secret_comm_data"}'
        self.cds._friends_db.set_comm_data_string(self.a_friend_id, old_comm_data_string)

        self.cds.activate_locking(self.passphrase)

        new_comm_data_string = self.cds._friends_db.get_comm_data_string(self.a_friend_id)
        self.assertFalse(old_comm_data_string == new_comm_data_string)

    def test_inactive_locking_set_new_comm_data(self):
        self.a_friend_id = self.cds._friends_db.add_friend('a_friend')
        comm_data_dict = {"secret": "öther_secret", "hostname": "ötherhost.org", "type": "tcp_aes", "port": 5678}
        self.cds.set_comm_data(self.a_friend_id, comm_data_dict)
        comm_data = self.cds.get_comm_data(self.a_friend_id)
        self.assertIn('secret', comm_data)
        self.assertEquals(comm_data['secret'], u'öther_secret')


class TestCommDataStoreUnlockWithoutLockingActive(unittest.TestCase):
    def setUp(self):
        self.cds = commdatastore.CommDataStore(":memory:", pydb.testing.guess_schema_dir())

        self.a_friend_id = self.cds._friends_db.add_friend('a_friend')
        self.cds._friends_db.set_comm_data_string(self.a_friend_id, '{"secret": "secret_comm_data"}')

    def test_empty(self):
        pass

    def test_unlock_without_locking_active(self):
        self.assertRaises(OverflowError, self.cds.unlock, "a passphrase")


class TestCommDataStoreDeriveKey(unittest.TestCase):
    def test_umlauts_in_passphrase_do_not_lead_to_crash(self):
        commdatastore._derive_key(u'ölölölöl', 'aaa', 5)


class TestCommDataStoreUnlock(unittest.TestCase):
    def setUp(self):
        self.passphrase = "hello123"

        self.cds = commdatastore.CommDataStore(":memory:", pydb.testing.guess_schema_dir())

        self.a_friend_id = self.cds._friends_db.add_friend('a_friend')
        self.cds._friends_db.set_comm_data_string(self.a_friend_id,
                                                  u'{"secret": "secret_comm_data", "hostname": "rüdstuff.org", '
                                                  '"type": "tcp_aes", "port": 1234}')
        commdatastore.default_iteration_count = 1  # speed up test cases

        self.cds.activate_locking(self.passphrase)

    def test_empty(self):
        pass

    def test_startup_locked(self):
        self.assertTrue(self.cds.is_locked())
        self.assertRaises(IOError, self.cds.get_comm_data, self.a_friend_id)

    def test_unlock_correct_secret(self):
        self.cds.unlock(self.passphrase)
        comm_data = self.cds.get_comm_data(self.a_friend_id)
        self.assertIn('secret', comm_data)
        self.assertEquals(comm_data['secret'], 'secret_comm_data')
        self.assertFalse(self.cds.is_locked())

    def test_unlock_wrong_secret(self):
        self.assertRaises(KeyError, self.cds.unlock, "not the passphrase")
        self.assertTrue(self.cds.is_locked())

    def test_unlock_correctly_and_set_new_comm_data(self):
        self.cds.unlock(self.passphrase)
        comm_data_dict = {"secret": "öther_secret", "hostname": "ötherhost.org", "type": "tcp_aes", "port": 5678}
        self.cds.set_comm_data(self.a_friend_id, comm_data_dict)
        comm_data = self.cds.get_comm_data(self.a_friend_id)
        self.assertIn('secret', comm_data)
        self.assertEquals(comm_data['secret'], u'öther_secret')

    def test_set_comm_data_without_unlock(self):
        comm_data_dict = {"secret": "öther_secret", "hostname": "ötherhost.org", "type": "tcp_aes", "port": 5678}
        self.assertRaises(IOError, self.cds.set_comm_data, self.a_friend_id, comm_data_dict)


if __name__ == '__main__':
    unittest.main()

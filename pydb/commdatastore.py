import friendsdb
import os
import pbkdf2
import com.securechannel.aeshmac_common
import crypto
import json
import base64

_canary_clear_text = "birdie"
_canary_friend_id = -1  # should not clash with an existing friend id

hash_fcn = 'sha512'
default_iteration_count = 60000
salt_length_bytes = 16


class CommDataStore:
    def __init__(self, db_file_path, schema_dir):
        self._friends_db = friendsdb.FriendsDB(db_file_path, schema_dir)
        self._unlocked = False

    def is_locking_active(self):
        return self._friends_db.is_locking_active()

    def is_locked(self):
        return not self._unlocked

    def activate_locking(self, passphrase):
        """ encrypts an unencrypted comm data store using passphrase
            raises an overflow error if the comm data is already encrypted
         """
        if self.is_locking_active():
            raise OverflowError("Is already locked")

        salt = os.urandom(salt_length_bytes)
        key = _derive_key(passphrase, salt, default_iteration_count)
        encrypted_canary = _encrypt(_canary_clear_text, key, _canary_friend_id)
        self._friends_db.set_locking_active(True, salt, default_iteration_count, encrypted_canary)
        friends = self._friends_db.get_friends()
        for friend in friends:
            comm_string = self._friends_db.get_comm_data_string(friend['id'])
            encrypted_comm_data = _encrypt(comm_string.encode('utf-8'), key, friend['id'])
            base64_comm_data = base64.b64encode(encrypted_comm_data)
            self._friends_db.set_comm_data_string(friend['id'], base64_comm_data)

    def unlock(self, passphrase):
        if not self.is_locking_active():
            raise OverflowError("Locking not active while trying to unlock")

        if not self._verify_passphrase(passphrase):
            raise KeyError("Wrong passphrase")

        self._unlocked = True

    def get_comm_data(self, friend_id):
        comm_data_from_db = self._friends_db.get_comm_data_string(friend_id)

        if not self.is_locking_active():
            return decode_comm_data_jason(comm_data_from_db)

        if not self._unlocked:
            raise IOError("Comm data is locked")

        comm_data_input_string = base64.b64decode(comm_data_from_db)
        comm_data_decrypted_string = _decrypt(comm_data_input_string, self.key, friend_id)
        comm_data = decode_comm_data_jason(comm_data_decrypted_string.decode('utf-8'))
        return comm_data

    def set_comm_data(self, friend_id, comm_data):
        comm_string = json.dumps(comm_data)
        if not self.is_locking_active():
            self._friends_db.set_comm_data_string(friend_id, comm_string)
            return

        if not self._unlocked:
            raise IOError("Comm data is locked")

        encrypted_comm_data = _encrypt(comm_string.encode('utf-8'), self.key, friend_id)
        base64_comm_data = base64.b64encode(encrypted_comm_data)
        self._friends_db.set_comm_data_string(friend_id, base64_comm_data)
        return

    def _verify_passphrase(self, passphrase):
        locking_info = self._friends_db.get_locking_info()
        salt = locking_info['salt']
        iteration_count = locking_info['iteration_count']
        encrypted_canary = str(locking_info['encrypted_canary'])

        key = _derive_key(passphrase, salt, iteration_count)
        encrypted_canary_test = _encrypt(_canary_clear_text, key, _canary_friend_id)

        if encrypted_canary_test == encrypted_canary:
            self.key = key
            return True

        return False


def _encrypt(content, key, friend_id):
    effective_key = com.securechannel.aeshmac_common.calc_hmac(key, str(friend_id))
    aes_ctr_instance = crypto.AesCtr(effective_key[:32])
    return aes_ctr_instance.encrypt(content)


def _decrypt(ciphertext, key, friend_id):
    effective_key = com.securechannel.aeshmac_common.calc_hmac(key, str(friend_id))
    aes_ctr_instance = crypto.AesCtr(effective_key[:32])
    return aes_ctr_instance.decrypt(ciphertext)


def _derive_key(passphrase, salt, iteration_count):
    passphrase_bytes = passphrase.encode('utf-8')
    return pbkdf2.py_pbkdf2_hmac(hash_fcn, passphrase_bytes, salt, iteration_count)


def decode_comm_data_jason(comm_data_string):
    if not comm_data_string:
        return {}
    return json.loads(comm_data_string)
import unittest

import pydb.crypto


class TestAesCtrInterfaceEncryption(unittest.TestCase):
    def setUp(self):
        self.initial_ctr_val = 0
        self.aes256_key = bytearray.fromhex('000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f')
        self.acc = pydb.crypto.AesCtr(self.aes256_key, self.initial_ctr_val)

    def test_empty(self):
        pass

    def test_simple_string_encryption(self):
        plaintext = b'hello'
        ciphertext = self.acc.encrypt(plaintext)
        self.assertNotEqual(plaintext, ciphertext)

    def test_encryption_and_decryption(self):
        plaintext = b'hello'
        ciphertext = self.acc.encrypt(plaintext)
        self.acc = pydb.crypto.AesCtr(self.aes256_key, self.initial_ctr_val)
        decrypted_text = self.acc.decrypt(ciphertext)
        self.assertEqual(plaintext, decrypted_text)


if __name__ == '__main__':
    unittest.main()

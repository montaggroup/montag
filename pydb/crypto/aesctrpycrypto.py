from Crypto.Cipher import AES
from Crypto.Util import Counter


class AesCtrPyCrypto(object):
    def __init__(self, aes_key, initial_counter_value=0):
        self.ctr = Counter.new(128, initial_value=initial_counter_value)
        self.aes = AES.new(aes_key, AES.MODE_CTR, counter=self.ctr)

    def _process(self, data):
        return self.aes.encrypt(data)

    def encrypt(self, plaintext):
        return self._process(plaintext)

    def decrypt(self, ciphertext):
        return self._process(ciphertext)
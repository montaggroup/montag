from pycryptopp.cipher import aes


class AesCtrPycryptopp:
    def __init__(self, aes_key, initial_counter_value=0):
        if initial_counter_value != 0:
            raise ValueError('This AES CTR implementation only supports counter start value 0.')
        self.aes = aes.AES(aes_key)

    def _process(self, data):
        return self.aes.process(data)

    def encrypt(self, plaintext):
        return self._process(plaintext)

    def decrypt(self, ciphertext):
        return self._process(ciphertext)



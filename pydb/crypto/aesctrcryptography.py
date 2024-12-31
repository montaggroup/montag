from cryptography.hazmat.primitives.ciphers import Cipher
from cryptography.hazmat.primitives.ciphers.algorithms import AES
from cryptography.hazmat.primitives.ciphers.modes import CTR


class AesCtrCryptography(object):
    def __init__(self, aes_key, initial_counter_value=0):
        self.cipher = Cipher(AES(aes_key), CTR(nonce=initial_counter_value.to_bytes(16, byteorder='big')))
        self.encrypttor = self.cipher.encryptor()
        self.decryptor = self.cipher.decryptor()


    def encrypt(self, plaintext):
        return self.encrypttor.update(plaintext)

    def decrypt(self, ciphertext):
        return self.decryptor.update(ciphertext)

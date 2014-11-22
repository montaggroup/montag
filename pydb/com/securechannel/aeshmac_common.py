import hashlib
import os
import hmac

KeyExchangeMaxMessageLength = 500


def get_nonce_512():
    entropy = os.urandom(512 / 8)
    return hashlib.sha512(entropy).digest()


def calc_hmac(hmac_shared_secret, msg):
    hmacgen = hmac.new(hmac_shared_secret, msg, hashlib.sha512)
    return hmacgen.digest()


def sha512d(msg):
    tmp_hash = hashlib.sha512(msg).digest()
    return hashlib.sha512(tmp_hash).digest()


def preshared_secrets(friend_data):
    return preshared_secrets_from_passphrase(friend_data['comm_data']['secret'])


def preshared_secrets_from_passphrase(passphrase):
    preshared_secret = sha512d(passphrase)
    preshared_secret_kex_cipher = preshared_secret[:32]
    preshared_secret_kex_hmac = preshared_secret[32:]

    return preshared_secret_kex_cipher, preshared_secret_kex_hmac

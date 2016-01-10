# coding=utf-8
# determine if pycryptopp or PyCrypto is available and set the aes ctr interface class accordingly
try:
    import aesctrpycryptopp
    AesCtr = aesctrpycryptopp.AesCtrPycryptopp
except ImportError:
    import aesctrpycrypto
    AesCtr = aesctrpycrypto.AesCtrPyCrypto

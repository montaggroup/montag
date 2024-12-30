# determine if pycryptopp or PyCrypto is available and set the aes ctr interface class accordingly
try:
    from pydb.crypto import aesctrpycryptopp
    AesCtr = aesctrpycryptopp.AesCtrPycryptopp
except ImportError:
    from pydb.crypto import aesctrpycrypto
    AesCtr = aesctrpycrypto.AesCtrPyCrypto

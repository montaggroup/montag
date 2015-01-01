import Pyro4

Pyro4.config.SERVERTYPE = "multiplex"
Pyro4.config.SOCK_REUSE = True
Pyro4.config.SERIALIZER = 'pickle'
Pyro4.config.SERIALIZERS_ACCEPTED = ['serpent', 'json', 'marshal', 'pickle']


def pydbserver():
    return Pyro4.Proxy('PYRO:pydb_server@localhost:4510')


def comm_data_store():
    return Pyro4.Proxy('PYRO:comm_data_store@localhost:4510')


def indexserver():
    return Pyro4.Proxy('PYRO:index_server@localhost:4512')


def comservice():
    return Pyro4.Proxy('PYRO:comservice@localhost:4513')


def fileserver():
    return Pyro4.Proxy('PYRO:fileserver@localhost:4514')


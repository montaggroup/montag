# coding=utf-8
import Pyro4

Pyro4.config.SERVERTYPE = "multiplex"
Pyro4.config.SOCK_REUSE = True
Pyro4.config.SERIALIZER = 'pickle'
Pyro4.config.SERIALIZERS_ACCEPTED = ['serpent', 'json', 'marshal', 'pickle']


def pydbserver():
    if False:  # trick ide into using the correct code insight
        import maindb
        return maindb.MainDB(None, None, None, None, None, None)

    return Pyro4.Proxy('PYRO:pydb_server@localhost:4510')


def comm_data_store():
    if False:  # trick ide into using the correct code insight
        import commdatastore
        return commdatastore.CommDataStore(None, None)

    return Pyro4.Proxy('PYRO:comm_data_store@localhost:4510')


def indexserver():
    if False:  # trick ide into using the correct code insight
        import indexserver as indexserver_
        return indexserver_.IndexServer(None, None)

    return Pyro4.Proxy('PYRO:index_server@localhost:4512')


def comservice():
    if False:  # trick ide into using the correct code insight
        import comservice as comservice_
        return comservice_.ComService(None)

    return Pyro4.Proxy('PYRO:comservice@localhost:4513')


def fileserver():
    if False:  # trick ide into using the correct code insight
        import fileserver as fileserver_
        return fileserver_.FileServer(None, None)

    return Pyro4.Proxy('PYRO:fileserver@localhost:4514')


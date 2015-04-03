import pydb.servers.services

def start_services():
    pydb.servers.services.stop_all_ignoring_exceptions()
    pydb.servers.services.start(pydb.servers.services.service_name('pydbserver'))
    pydb.servers.services.start(pydb.servers.services.service_name('indexserver'))


def stop_services():
    pydb.servers.services.stop_all_ignoring_exceptions()

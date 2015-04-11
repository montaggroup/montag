import pydb.services


def start_services(fileserver=False):
    pydb.services.stop_all_ignoring_exceptions()
    pydb.services.start(pydb.services.service_name('pydbserver'))
    pydb.services.start(pydb.services.service_name('indexserver'))
    if fileserver:
        pydb.services.start(pydb.services.service_name('fileserver'))


def stop_services():
    pydb.services.stop_all_ignoring_exceptions()

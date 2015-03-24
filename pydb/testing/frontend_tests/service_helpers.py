import pydb.services


def start_services(service_base_names=('pydbserver', 'indexserver')):
    pydb.services.stop_all()

    for service_base_name in service_base_names:
        pydb.services.start(pydb.services.service_name(service_base_name))


def stop_services(ignore_exceptions=True):
    pydb.services.stop_all(ignore_exceptions=ignore_exceptions)

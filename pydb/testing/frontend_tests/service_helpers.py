import pydb.services
import pydb.testing


def start_services(testcase_folder, fileserver=False):
    pydb.services.stop_all_ignoring_exceptions()
    pydb.services.start(pydb.services.service_name('pydbserver'), base_dir_path=testcase_folder)
    pydb.services.start(pydb.services.service_name('indexserver'), base_dir_path=testcase_folder)
    if fileserver:
        pydb.services.start(pydb.services.service_name('fileserver'), base_dir_path=testcase_folder)


def stop_services():
    pydb.services.stop_all_ignoring_exceptions()

import pydb.services
import pydb.testing


def start_services(testcase_name, fileserver=False):
    base_dir_name = testcase_name.replace("/", "_").replace("..", "_")
    base_dir_path = pydb.testing.get_clean_temp_dir(base_dir_name)

    pydb.services.stop_all_ignoring_exceptions()
    pydb.services.start(pydb.services.service_name('pydbserver'), base_dir_path=base_dir_path)
    pydb.services.start(pydb.services.service_name('indexserver'), base_dir_path=base_dir_path)
    if fileserver:
        pydb.services.start(pydb.services.service_name('fileserver'), base_dir_path=base_dir_path)


def stop_services():
    pydb.services.stop_all_ignoring_exceptions()

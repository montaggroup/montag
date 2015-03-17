import os


def get_testdata_path(file_name):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), 'test_data', file_name))

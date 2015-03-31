import os
import shutil


def guess_schema_dir():
    if os.path.exists("db-schemas"):
        return "db-schemas"

    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'db-schemas'))


def get_base_temp_dir():
    parent_folder = os.path.dirname(__file__)
    base_temp_dir = os.path.join(parent_folder, "temp")
    if not os.path.exists(base_temp_dir):
        os.mkdir(base_temp_dir)
    return base_temp_dir


def get_clean_temp_dir(name):
    """ creates a directory identified by name in the test temp structure
    if the directory existed beforehand, it will be cleared
    :param name:
    :return:
    """
    assert('/' not in name)
    assert('\\' not in name)
    assert('..' not in name)

    base = get_base_temp_dir()
    clean_temp_dir = os.path.join(base, name)
    if os.path.exists(clean_temp_dir):
        shutil.rmtree(clean_temp_dir)
    os.mkdir(clean_temp_dir)
    return clean_temp_dir
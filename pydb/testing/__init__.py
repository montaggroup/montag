import os


def guess_schema_path():
    if os.path.exists("db-schemas"):
        return "db-schemas"

    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'db-schemas'))

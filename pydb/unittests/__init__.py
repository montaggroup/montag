import os


def guess_schema_path():
    if os.path.exists("db-schemas"):
        return "db-schemas"
    return "../../db-schemas"
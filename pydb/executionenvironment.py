import imp
import sys
import os


def using_py2exe():
    return (hasattr(sys, "frozen") or  # new py2exe
            hasattr(sys, "importers") or  # old py2exe
            imp.is_frozen("__main__"))  # tools/freeze


def get_main_dir():
    if using_py2exe():
        return os.path.dirname(sys.executable)
    return os.path.dirname(sys.argv[0])
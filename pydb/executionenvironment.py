import imp
import sys
import re
import getpass
import os

def script_extension():
    if using_py2exe():
        return "exe"
    else:
        return "py"


def python_binary_to_use_for_scripts():
    return sys.executable


def base_args_to_start_service(service_name):
    startargs = []
    if not using_py2exe():
        startargs.append(python_binary_to_use_for_scripts())
    startargs.append(service_name)
    return startargs


def is_montag_process(process_info, candidate_names):
    # skip windows system or idle process
    if process_info['username'] is None:
        return

    # remove domain name on windows
    process_username = re.sub(r".*\\", "", process_info['username'])

    if process_username != getpass.getuser():
        return

    name = process_info['name'].lower()

    if using_py2exe():
        for srv in candidate_names:
            if srv.lower() in name:
                return srv

    else:
        if name == 'python' or name == 'python2.7' or name == 'python.exe':
            for arg in process_info['cmdline']:
                for srv in candidate_names:
                    if srv in arg:
                        return srv


def using_py2exe():
    return (hasattr(sys, "frozen") or  # new py2exe
            hasattr(sys, "importers") or  # old py2exe
            imp.is_frozen("__main__"))  # tools/freeze


def get_main_dir():
    if using_py2exe():
        return os.path.dirname(sys.executable)
    return os.path.dirname(sys.argv[0])
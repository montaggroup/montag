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


def base_args_to_start_service(service_executable):
    start_args = []
    if not using_py2exe():
        start_args.append(python_binary_to_use_for_scripts())

    services_dir = os.path.join(os.path.dirname(__file__), '..')
    service_dir = os.path.relpath(services_dir)

    if service_dir == '.':  # ./ makes the ps output less nice
        path_to_service_executable = service_executable
    else:
        path_to_service_executable = os.path.join(service_dir, service_executable)

    start_args.append(path_to_service_executable)
    return start_args


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
        if name in ('python', 'python3', 'python.exe', 'python3.exe'):
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


def get_schema_dir():
    return os.path.join(get_main_dir(), "db-schemas")


def determine_database_directory(override_base_dir=None):
    if override_base_dir is None:
        base_dir = get_main_dir()
    else:
        base_dir = override_base_dir

    return os.path.join(base_dir, "db")

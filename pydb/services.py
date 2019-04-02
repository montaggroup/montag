# coding=utf-8
import tempfile
import os
import getpass
import psutil
import signal

import pydb.executionenvironment as executionenvironment

# configuration options

log_path = tempfile.gettempdir()

# end of configuration options

SERVICE_WAIT_TIMEOUT = 10
DEFAULT_LOG_LEVEL = 'INFO'
SERVICE_PREFIX = 'montag-'
BASENAMES = ["pydbserver", "comserver", "comservice", "indexserver", "fileserver", "web2py", "importer"]
SCRIPT_EXTENSION = executionenvironment.script_extension()
DEFAULT_ATTRIBUTES_FOR_PSUTIL_AS_DICT = ['name', 'exe', 'username', 'status', 'cmdline']


def service_name(base_name):
    return SERVICE_PREFIX + base_name + "." + SCRIPT_EXTENSION


all_service_names = [service_name(basename) for basename in BASENAMES]


def _get_default_services_status():
    services_status = dict()

    for service in all_service_names:
        services_status[service] = {'status': 'not running', 'pid': None, 'process': None}

    return services_status


def maybe_parent_service_process(service_process):
    try:
        while executionenvironment.is_montag_process(
                service_process.parent().as_dict(attrs=DEFAULT_ATTRIBUTES_FOR_PSUTIL_AS_DICT), all_service_names):
            service_process = service_process.parent()
    except psutil.AccessDenied:
        pass

    return service_process


def get_current_services_status():
    services_status = _get_default_services_status()
    already_seen = set()
    try:
        for p in psutil.process_iter(attrs=DEFAULT_ATTRIBUTES_FOR_PSUTIL_AS_DICT):
            detected_service_name = executionenvironment.is_montag_process(p.info, all_service_names)
            if detected_service_name is not None:
                if detected_service_name not in already_seen:
                    p = maybe_parent_service_process(p)
                    services_status[detected_service_name] = {'status': p.status(), 'pid': p.pid, 'process': p}
                    already_seen.add(detected_service_name)
    except psutil.AccessDenied:
        pass

    return services_status


def logfile_path(service_name_, log_file_base_path=log_path):
    return os.path.join(log_file_base_path, getpass.getuser() + '-' + service_name_.replace('.py', '.log').
                        replace('.exe', '.log'))


def start(service_name_, log_level=DEFAULT_LOG_LEVEL, base_dir_path=None, log_file_base_path=log_path):
    startargs = executionenvironment.base_args_to_start_service(service_name_)
    startargs.append('--loglevel')
    startargs.append(log_level)

    if base_dir_path is not None:
        startargs.append('--basepath')
        startargs.append(base_dir_path)

    try:
        with open(logfile_path(service_name_, log_file_base_path=log_file_base_path), 'wb', 1) as logfile:
            p = psutil.Popen(startargs, stdout=logfile, stderr=logfile)
            logfile.flush()
            return_code = p.wait(timeout=1)
            if return_code:
                raise EnvironmentError("Service {} did not start up correctly".format(service_name_))
    except psutil.TimeoutExpired:
        pass
    else:
        raise EnvironmentError("Unable to start service {}".format(service_name_))


def kill_process_tree(pid, sig=signal.SIGTERM, include_parent=True,
                      timeout=None, on_terminate=None):
    """Kill a process tree (including grandchildren) with signal
    "sig" and return a (gone, still_alive) tuple.
    "on_terminate", if specified, is a callaback function which is
    called as soon as a child terminates.
    Taken from psutil recipes
    """
    assert pid != os.getpid(), "won't kill myself"
    parent = psutil.Process(pid)
    children = parent.children(recursive=True)
    if include_parent:
        children.append(parent)
    for p in children:
        p.send_signal(sig)
    gone, alive = psutil.wait_procs(children, timeout=timeout,
                                    callback=on_terminate)
    return gone, alive


def stop(pid):
    gone, alive = kill_process_tree(pid, timeout=SERVICE_WAIT_TIMEOUT)
    if alive:

        for p in alive:
            try:
                p.kill()
            except psutil.NoSuchProcess:
                pass

        psutil.wait_procs(alive, timeout=SERVICE_WAIT_TIMEOUT)


def stop_all_ignoring_exceptions(verbose=False, name_filter_fct=lambda x: True):
    services_status = get_current_services_status()
    for name in filter(name_filter_fct, all_service_names[::-1]):
        status = services_status[name]
        if status['status'] != 'not running':
            if verbose:
                print 'stopping service {}'.format(name)
            # noinspection PyBroadException
            try:
                stop(status['pid'])
            except Exception as e:
                print 'could not stop service {}: {}'.format(name, e)

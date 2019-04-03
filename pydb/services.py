# coding=utf-8
import tempfile
import os
import getpass
import pydb.executionenvironment as executionenvironment
import psutil

# configuration options

log_path = tempfile.gettempdir()

# end of configuration options

DEFAULT_LOG_LEVEL = 'INFO' 

service_prefix = 'montag-'
basenames = ["pydbserver", "comserver", "comservice", "indexserver", "fileserver", "web2py", "importer"]

extension = executionenvironment.script_extension()

PSUTIL2 = psutil.version_info >= (2, 0)


def service_name(base_name):
    return service_prefix + base_name + "." + extension

names = [service_name(basename) for basename in basenames]


def pidlist():
    if PSUTIL2:
        return psutil.pids()
    else:
        return psutil.get_pid_list()


def _get_default_services_status():
    services_status = dict()
    for service in names:
        services_status[service] = {'status': 'not running', 'pid': 0}
    return services_status


# noinspection PyDefaultArgument
def as_dict_for_monkey_patching_old_psutils(self, attrs=[], ad_value=None):
    """Utility method returning process information as a hashable
    dictionary.

    If 'attrs' is specified it must be a list of strings reflecting
    available Process class's attribute names (e.g. ['get_cpu_times',
    'name']) else all public (read only) attributes are assumed.

    'ad_value' is the value which gets assigned to a dict key in case
    AccessDenied exception is raised when retrieving that particular
    process information.
    """
    excluded_names = {'send_signal', 'suspend', 'resume', 'terminate', 'kill', 'wait', 'is_running', 'as_dict',
                      'parent', 'get_children', 'nice', 'get_rlimit'}
    retdict = dict()
    for name in set(attrs or dir(self)):
        if name.startswith('_'):
            continue
        if name.startswith('set_'):
            continue
        if name in excluded_names:
            continue
        try:
            attr = getattr(self, name)
            if callable(attr):
                if name == 'get_cpu_percent':
                    ret = attr(interval=0)
                else:
                    ret = attr()
            else:
                ret = attr
        except psutil.AccessDenied:
            ret = ad_value
        except NotImplementedError:
            # in case of not implemented functionality (may happen
            # on old or exotic systems) we want to crash only if
            # the user explicitly asked for that particular attr
            if attrs:
                raise
            continue
        if name.startswith('get'):
            if name[3] == '_':
                name = name[4:]
            elif name == 'getcwd':
                name = 'cwd'
        retdict[name] = ret
    return retdict
                                                                                                                                                                                                                                                                                                
if not hasattr(psutil.Process, 'as_dict'):
    psutil.Process.as_dict = as_dict_for_monkey_patching_old_psutils


def get_current_services_status():
    services_status = _get_default_services_status()
    for pid in pidlist():
        try:
            p = psutil.Process(pid)
            pinfo = p.as_dict(attrs=['name', 'exe', 'username', 'status', 'cmdline'])

            detected_service_name = executionenvironment.is_montag_process(pinfo, names)
            if detected_service_name is not None:
                services_status[detected_service_name] = {'status': pinfo['status'], 'pid': pid, 'process': p}
        except (psutil.AccessDenied, psutil.NoSuchProcess):
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


def stop(service_process):
    """ service_process is the content of the 'process' key in service status dict of the service to stop
    this function may throw a (yet) unspecified exception
    """
    service_process.terminate()
    service_process.wait(timeout=5)


def stop_all_ignoring_exceptions(verbose=False, name_filter_fct=lambda x: True):
    services_status = get_current_services_status()
    for name in filter(name_filter_fct, names[::-1]):
        if services_status[name]['status'] != 'not running':
            if verbose:
                print 'stopping service {}'.format(name)
            # noinspection PyBroadException
            try:
                stop(services_status[name]['process'])
            except Exception:
                print 'could not stop service {}' .format(name)
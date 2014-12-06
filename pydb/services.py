import tempfile
import os
import getpass
import re
from pydb.executionenvironment import using_py2exe
import psutil

# configuration options

log_path = tempfile.gettempdir()
log_level = 'WARNING'  # see pyro log levels

# end of configuration options

service_prefix = 'montag-'

basenames = ["pydbserver", "comserver", "comservice", "indexserver", "web2py"]

if using_py2exe():
    names = [service_prefix + name + ".exe" for name in basenames]
else:
    names = [service_prefix + name + ".py" for name in basenames]

PSUTIL2 = psutil.version_info >= (2, 0)


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
    for service_name in set(attrs or dir(self)):
        if service_name.startswith('_'):
            continue
        if service_name.startswith('set_'):
            continue
        if service_name in excluded_names:
            continue
        try:
            attr = getattr(self, service_name)
            if callable(attr):
                if service_name == 'get_cpu_percent':
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
        if service_name.startswith('get'):
            if service_name[3] == '_':
                service_name = service_name[4:]
            elif service_name == 'getcwd':
                service_name = 'cwd'
        retdict[service_name] = ret
    return retdict


if not hasattr(psutil.Process, 'as_dict'):
    psutil.Process.as_dict = as_dict_for_monkey_patching_old_psutils


def get_current_services_status():
    services_status = _get_default_services_status()
    for pid in pidlist():
        try:
            p = psutil.Process(pid)
            pinfo = p.as_dict(attrs=['name', 'exe', 'username', 'status', 'cmdline'])

            # skip windows system or idle process
            if pinfo['username'] is None:
                continue
            # remove domain name on windows
            process_username = re.sub(r".*\\", "", pinfo['username'])

            if using_py2exe():
                if process_username == getpass.getuser():
                    for srv in names:
                        if srv.lower() in pinfo['name'].lower():
                            services_status[srv] = {'status': p.status, 'pid': pid, 'process': p}
            else:
                name = pinfo['name']
                if (name == 'python' or name == 'python2.7' or name == 'python.exe') and \
                                process_username == getpass.getuser():
                    for arg in pinfo['cmdline']:
                        for srv in names:
                            if srv in arg:
                                services_status[srv] = {'status': pinfo['status'], 'pid': pid, 'process': p}
        except psutil.AccessDenied:
            pass

    return services_status


def logfile_path(service_name):
    return os.path.join(log_path, getpass.getuser() + '-' + service_name.replace('.py', '.log').replace('.exe', '.log'))


def start(service_name):
    startargs = []
    if not using_py2exe():
        startargs.append('python2.7')
    startargs.append(service_name)
    env = os.environ
    env['PYRO_LOGLEVEL'] = log_level
    env['PYRO_LOGFILE'] = '{stderr}'
    try:
        with open(logfile_path(service_name), 'wb', 1) as logfile:
            p = psutil.Popen(startargs, env=env, stdout=logfile, stderr=logfile)
            logfile.flush()
            return_code = p.wait(timeout=1)
            if return_code:
                raise EnvironmentError("Service {} did not start up correctly".format(service_name))
    except psutil.TimeoutExpired:
        pass
    else:
        raise EnvironmentError("Unable to start service {}".format(service_name))


def stop(service_process):
    """ service_process is the content of the 'process' key in service status dict of the service to stop
    this function may throw a (yet) unspecified exception
    """
    service_process.terminate()
    service_process.wait(timeout=5)

import subprocess
import tempfile
import Pyro4
import sys
import os
import platform
from pydb.executionenvironment import using_py2exe

sys.excepthook = Pyro4.util.excepthook


def create_server(data_dir=None, port="4510", sync_mode=True, debug=False, basedir="."):
    if not data_dir:
        data_dir = tempfile.mkdtemp(dir='.')
    os.environ["PYRO_LOGFILE"] = '{stderr}'

    if debug:
        os.environ["PYRO_LOGLEVEL"] = 'DEBUG'

    commands = [os.path.join(basedir, "montag-pydbserver.py")]
    shell = False
    if using_py2exe():
        commands = [os.path.join(basedir, "montag-pydbserver.exe")]
        shell = True
    elif platform.system() == 'Windows':
        commands = [r"c:\python27\python", os.path.join(basedir, "montag-pydbserver.py")]
        shell = True

    server_args = commands + ["-b", data_dir, "-n", "pydb_server", "-p", str(port)]
    if not sync_mode:
        server_args.append("--no-sync")

    server = subprocess.Popen(server_args, env=os.environ, shell=shell)
    db = Pyro4.Proxy('PYRO:pydb_server@localhost:%s' % port)    # use name server object lookup uri shortcut
    db.testing_server = server
    while True:
        # noinspection PyBroadException
        try:
            if db.ping() != "pong":
                print("Unable to talk", file=sys.stderr)
                sys.exit(-1)
            return db
        except Exception:
            pass


def stop_server(db):
    db.testing_server.terminate()


class Server(object):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

        self.db = None

    def __enter__(self):
        self.db = create_server(*self.args, **self.kwargs)
        return self.db

    # noinspection PyUnusedLocal,PyShadowingBuiltins
    def __exit__(self, type, value, traceback):
        stop_server(self.db)

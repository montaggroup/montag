#!/usr/bin/env python2.7
import logging

logging.basicConfig(level=logging.DEBUG)

import Pyro4
import argparse
import os
import time
import sys
from pydb.executionenvironment import using_py2exe
import pydb.indexserver


def get_main_dir():
    if using_py2exe():
        return os.path.dirname(sys.executable)
    return os.path.dirname(sys.argv[0])


if __name__ == "__main__":
    import pydb.pyrosetup

    base_path = get_main_dir()

    parser = argparse.ArgumentParser(description='Runs the indexing server')
    parser.add_argument('--basepath', '-b', dest='basepath', help='Sets the basepath for the server', action='store')
    parser.add_argument('--name', '-n', dest='pyro_name', help='Sets the Pyro4 name for the server', action='store',
                        default="index_server")
    parser.add_argument('--port', '-p', dest='pyro_port', help='Sets the Pyro4 port for the server', action='store',
                        default=4512, type=int)

    args = parser.parse_args()

    logger = logging.getLogger('indexserver')
    logger.info('### logging started at %s local time. ###', time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime()))

    index_server = pydb.indexserver.IndexServer(base_path)

    daemon = Pyro4.Daemon(port=args.pyro_port)  # make a Pyro daemon

    uri = daemon.register(index_server, objectId=args.pyro_name)  # register the db object as a Pyro object
    daemon.requestLoop()  # start the event loop of the server to wait for calls
    index_server.stop()


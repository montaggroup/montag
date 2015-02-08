#!/usr/bin/env python2.7
import logging

logging.basicConfig(level=logging.INFO)

import Pyro4
import pydb.fileserver
import argparse
import os
import time
from pydb.executionenvironment import get_main_dir
import pydb.commdatastore
import pydb.pyrosetup
import pydb.config
import pydb.logconfig

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Runs the file server')
    parser.add_argument('--basepath', '-b', dest='basepath', help='Sets the basepath for the server', action='store')
    parser.add_argument('--name', '-n', dest='pyro_name', help='Sets the Pyro4 name for the server', action='store',
                        default="fileserver")
    parser.add_argument('--port', '-p', dest='pyro_port', help='Sets the Pyro4 port for the server', action='store',
                        default=4514, type=int)
    parser.add_argument('--no-sync', dest='no_sync',
                        help='Disable database sync - may lead to COMPLETE data loss on error (eg. power failure)',
                        action="store_true", default=False)

    pydb.logconfig.add_log_level_to_parser(parser)

    args = parser.parse_args()

    pydb.logconfig.set_log_level(args.loglevel)
    pydb.config.read_config()

    logger = logging.getLogger('fileserver')
    logger.info('### logging started at %s local time. ###', time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime()))

    if args.basepath is None:
        base_path = get_main_dir()
    else:
        base_path = args.basepath

    # todo: read from config files
    store_dir = os.path.join(base_path, "filestore")
    if not os.path.exists(store_dir):
        os.mkdir(store_dir)

    file_server = pydb.fileserver.build(store_dir, pydb.pyrosetup.pydbserver())

    daemon = Pyro4.Daemon(port=args.pyro_port)

    daemon.register(file_server, objectId=args.pyro_name)

    daemon.requestLoop()        



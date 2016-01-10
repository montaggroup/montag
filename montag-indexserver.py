#!/usr/bin/env python2.7
# coding=utf-8
import logging
import argparse
import time

import Pyro4

from pydb.executionenvironment import determine_database_directory, get_schema_dir
import pydb.indexserver
import pydb.config
import pydb.logconfig

logging.basicConfig(level=logging.INFO)


if __name__ == "__main__":
    import pydb.pyrosetup

    parser = argparse.ArgumentParser(description='Runs the indexing server')
    parser.add_argument('--basepath', '-b', dest='basepath', help='Sets the base path for the server', action='store')
    parser.add_argument('--name', '-n', dest='pyro_name', help='Sets the Pyro4 name for the server', action='store',
                        default="index_server")
    parser.add_argument('--port', '-p', dest='pyro_port', help='Sets the Pyro4 port for the server', action='store',
                        default=4512, type=int)
    pydb.logconfig.add_log_level_to_parser(parser)

    args = parser.parse_args()

    pydb.logconfig.set_log_level(args.loglevel)

    logger = logging.getLogger('indexserver')
    logger.info('### logging started at %s local time. ###', time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime()))

    db_dir = determine_database_directory(args.basepath)
    pydb.config.read_config()
    index_server = pydb.indexserver.build(db_dir, schema_dir=get_schema_dir())
    index_server.start()

    daemon = Pyro4.Daemon(port=args.pyro_port)  # make a Pyro daemon

    uri = daemon.register(index_server, objectId=args.pyro_name)  # register the db object as a Pyro object
    daemon.requestLoop()  # start the event loop of the server to wait for calls
    index_server.stop()


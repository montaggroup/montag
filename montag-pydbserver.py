#!/usr/bin/env python2.7
# coding=utf-8
import logging
import argparse
import os
import time
import atexit

import Pyro4

import pydb.maindb
from pydb.executionenvironment import get_schema_dir, determine_database_directory
import pydb.commdatastore
import pydb.config
import pydb.logconfig

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    import pydb.pyrosetup

    parser = argparse.ArgumentParser(description='Runs the catalogue server')
    parser.add_argument('--basepath', '-b', dest='basepath', help='Sets the base path for the server', action='store')
    parser.add_argument('--name', '-n', dest='pyro_name', help='Sets the Pyro4 name for the server', action='store',
                        default="pydb_server")
    parser.add_argument('--comm_data_store_name', '-c', dest='comm_data_store_name',
                        help='Sets the Pyro4 name for the comm data store', action='store', default="comm_data_store")
    parser.add_argument('--port', '-p', dest='pyro_port', help='Sets the Pyro4 port for the server', action='store',
                        default=4510, type=int)
    parser.add_argument('--no-sync', dest='no_sync',
                        help='Disable database sync - may lead to COMPLETE data loss on error (eg. power failure)',
                        action="store_true", default=False)
    pydb.logconfig.add_log_level_to_parser(parser)

    args = parser.parse_args()

    pydb.logconfig.set_log_level(args.loglevel)

    logger = logging.getLogger('pydbserver')
    logger.info('### logging started at %s local time. ###', time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime()))

    pydb.config.read_config()
    db_dir = determine_database_directory(args.basepath)
    main_db = pydb.maindb.build(db_dir, schema_dir=get_schema_dir(), enable_db_sync=not args.no_sync)

    def term_handler():
        main_db.hard_commit_all()

    atexit.register(term_handler)

    daemon = Pyro4.Daemon(port=args.pyro_port)
    daemon.register(main_db, objectId=args.pyro_name)

    comm_data_store = pydb.commdatastore.CommDataStore(os.path.join(db_dir, 'friends.db'), get_schema_dir())
    daemon.register(comm_data_store, objectId=args.comm_data_store_name)

    daemon.requestLoop()        

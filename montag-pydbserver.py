#!/usr/bin/env python2.7
import logging

logging.basicConfig(level=logging.DEBUG)

import Pyro4
import pydb.maindb
import argparse
import os
import time
import atexit
import sys
from pydb.executionenvironment import using_py2exe
import pydb.commdatastore


def get_main_dir():
    if using_py2exe():
        return os.path.dirname(sys.executable)
    return os.path.dirname(sys.argv[0])


def schema_path():
    return os.path.join(get_main_dir(), "db-schemas")


if __name__ == "__main__":
    import pydb.pyrosetup

    parser = argparse.ArgumentParser(description='Runs the server')
    parser.add_argument('--basepath', '-b', dest='basepath', help='Sets the basepath for the server', action='store')
    parser.add_argument('--name', '-n', dest='pyro_name', help='Sets the Pyro4 name for the server', action='store',
                        default="pydb_server")
    parser.add_argument('--comm_data_store_name', '-c', dest='comm_data_store_name',
                        help='Sets the Pyro4 name for the comm data store', action='store', default="comm_data_store")
    parser.add_argument('--port', '-p', dest='pyro_port', help='Sets the Pyro4 port for the server', action='store',
                        default=4510, type=int)
    parser.add_argument('--no-sync', dest='no_sync',
                        help='Disable database sync - may lead to COMPLETE data loss on error (eg. power failure)',
                        action="store_true", default=False)

    args = parser.parse_args()

    logger = logging.getLogger('pydbserver')
    logger.info('### logging started at %s local time. ###', time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime()))

    if args.basepath is None:
        basepath = get_main_dir()
    else:
        basepath = args.basepath

    maindb = pydb.maindb.build(basepath, schema_path=schema_path(), enable_db_sync=not args.no_sync)

    def term_handler():
        maindb.hard_commit_all()

    atexit.register(term_handler)

    print "Pyro port: {}".format(args.pyro_port)
    daemon = Pyro4.Daemon(port=args.pyro_port)

    pydb_uri = daemon.register(maindb, objectId=args.pyro_name)
    print "PYRO Server URI: {}".format(str(pydb_uri))

    comm_data_store = pydb.commdatastore.CommDataStore(os.path.join(basepath, 'db', 'friends.db'), schema_path())
    comm_datas_store_uri = daemon.register(comm_data_store, objectId=args.comm_data_store_name)

    daemon.requestLoop()        



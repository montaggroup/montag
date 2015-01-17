#!/usr/bin/env python2.7
import logging

logging.basicConfig(level=logging.DEBUG)

import Pyro4
import pydb.comservice

import argparse
import multiprocessing
from twisted.python import log

import pydb.config

pydb.config.read_config()

observer = log.PythonLoggingObserver()
observer.start()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    import pydb.pyrosetup

    cs = pydb.comservice.build()

    parser = argparse.ArgumentParser(description='Runs the communication client service')
    parser.add_argument('--name', '-n', dest='pyro_name', help='Sets the Pyro4 name for the server', action='store',
                        default="comservice")
    parser.add_argument('--port', '-p', dest='pyro_port', help='Sets the Pyro4 port for the server', action='store',
                        default=4513, type=int)

    args = parser.parse_args()

    print "Pyro port: %s" % (args.pyro_port)
    daemon = Pyro4.Daemon(port=args.pyro_port)  # make a Pyro daemon

    commserver_uri = daemon.register(cs, objectId=args.pyro_name)  # register the db object as a Pyro object
    print "Comm Service PYRO Server URI: " + str(commserver_uri)

    daemon.requestLoop()  # start the event loop of the server to wait for calls
    cs.stop()


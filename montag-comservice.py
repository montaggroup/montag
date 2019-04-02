#!/usr/bin/env python2.7
# coding=utf-8
import logging
import argparse
import multiprocessing

import Pyro4

import pydb.comservice
import pydb.config
import pydb.logconfig

pydb.config.read_config()
pydb.logconfig.catch_twisted_log_messages()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    import pydb.pyrosetup

    cs = pydb.comservice.build()

    parser = argparse.ArgumentParser(description='Runs the communication client service')
    parser.add_argument('--basepath', '-b', dest='basepath', help='Sets the basepath for the server', action='store')
    parser.add_argument('--name', '-n', dest='pyro_name', help='Sets the Pyro4 name for the server', action='store',
                        default="comservice")
    parser.add_argument('--port', '-p', dest='pyro_port', help='Sets the Pyro4 port for the server', action='store',
                        default=4513, type=int)
    pydb.logconfig.add_log_level_to_parser(parser)

    args = parser.parse_args()

    pydb.logconfig.set_log_level(args.loglevel)

    print "Pyro port: %s" % args.pyro_port
    daemon = Pyro4.Daemon(port=args.pyro_port)  # make a Pyro daemon

    commserver_uri = daemon.register(cs, objectId=args.pyro_name)  # register the db object as a Pyro object
    print "Comm Service PYRO Server URI: " + str(commserver_uri)

    daemon.requestLoop()  # start the event loop of the server to wait for calls
    cs.stop()


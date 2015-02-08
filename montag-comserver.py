#!/usr/bin/env python2.7

import logging
logging.basicConfig(level=logging.INFO)

from twisted.internet import reactor
from pydb.com.server import Server
import pydb.config as config
from twisted.python import log
import argparse

import pydb.config
import pydb.logconfig

pydb.config.read_config()

observer = log.PythonLoggingObserver()
observer.start()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Runs the communication server')
    pydb.logconfig.add_log_level_to_parser(parser)

    args = parser.parse_args()

    pydb.logconfig.set_log_level(args.loglevel)

    s = Server(tcp_port_number=config.comserver_port(),
               upload_rate_limit_kbps=config.upload_rate_limit_kbytes_per_second())

    reactor.run()


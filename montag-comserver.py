#!/usr/bin/env python2.7
# coding=utf-8

import argparse

from twisted.internet import reactor

from pydb.com.server import Server
import pydb.config as config
import pydb.logconfig


if __name__ == "__main__":
    pydb.config.read_config()
    pydb.logconfig.catch_twisted_log_messages()

    parser = argparse.ArgumentParser(description='Runs the communication server')
    parser.add_argument('--basepath', '-b', dest='basepath', help='Sets the basepath for the server', action='store')
    pydb.logconfig.add_log_level_to_parser(parser)

    args = parser.parse_args()

    pydb.logconfig.set_log_level(args.loglevel)

    s = Server(tcp_port_number=config.comserver_port(),
               upload_rate_limit_kbps=config.upload_rate_limit_kbytes_per_second(), reactor=reactor)

    reactor.run()


#!/usr/bin/env python2.7

import logging
logging.basicConfig(level=logging.DEBUG)

from twisted.internet import reactor
from pydb.com.server import Server
import pydb.config as config
from twisted.python import log

import pydb.config

pydb.config.read_config()

observer = log.PythonLoggingObserver()
observer.start()

s = Server(tcp_port_number=config.comserver_port(),
           upload_rate_limit_kbps=config.upload_rate_limit_kbytes_per_second())

reactor.run()


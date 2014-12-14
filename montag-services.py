#!/usr/bin/env python2.7
import logging
logging.basicConfig(level=logging.DEBUG)

import argparse
import sys
import pydb.services as services
import time
import pydb.pyrosetup

def do_list_services(args):
    services_status = services.get_current_services_status()
    for name in services_status.keys():
        print 'service %s is %s (pid=%d)' % (name, services_status[name]['status'], services_status[name]['pid'])


def do_start_services(args):
    services.log_level = args.log_level
    services.log_path = args.log_path

    services_status = services.get_current_services_status()
    for name in services.names:
        if services_status[name]['status'] == 'not running':
            print 'starting service {}, log {}'.format(name, services.logfile_path(name))
            try:
                services.start(name)
                if 'pydbserver' in name:  # allow service to start up
                    _wait_for_db_ping_ok()
            except EnvironmentError:
                print 'could not start service %s' % name
                sys.exit(1)


def _wait_for_db_ping_ok():
    db = pydb.pyrosetup.pydbserver()
    while db.ping() != 'pong':
        time.sleep(0.5)


def do_stop_services(args):
    services_status = services.get_current_services_status()
    for name in services.names[::-1]:
        if services_status[name]['status'] != 'not running':
            print 'stopping service {}'.format(name)
            try:
                services.stop(services_status[name]['process'])
            except Exception:
                print 'could not stop service %s' % name


def do_restart_services(args):
    do_stop_services(args)
    do_start_services(args)


parser = argparse.ArgumentParser(description='Controls and lists montag services.')

subparsers = parser.add_subparsers(help='sub-command help')

parser_list = subparsers.add_parser('status', help='list services status')
parser_list.set_defaults(func=do_list_services)

parser_start = subparsers.add_parser('start', help='start services')
parser_start.add_argument('--log-level', '-L', help='Start services with log level', dest='log_level')
parser_start.add_argument('--log-path', '-P', help='set services log path', dest='log_path')
parser_start.set_defaults(func=do_start_services, debug=False, log_level='WARNING', log_path=services.log_path)

parser_stop = subparsers.add_parser('stop', help='stop services')
parser_stop.set_defaults(func=do_stop_services)

parser_restart = subparsers.add_parser('restart', help='stop services')
parser_restart.add_argument('--log-level', '-L', help='Start services with log level', dest='log_level')
parser_restart.add_argument('--log-path', '-P', help='set services log path', dest='log_path')
parser_restart.set_defaults(func=do_restart_services, debug=False, log_level='WARNING', log_path=services.log_path)

args = parser.parse_args()

args.func(args)

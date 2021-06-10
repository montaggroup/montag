#!/usr/bin/env python2.7
# coding=utf-8
import argparse
import sys
import time

import Pyro4
import Pyro4.errors

import pydb.services as services
import pydb.pyrosetup
import pydb.config


def do_list_services(_):
    services_status = services.get_current_services_status()
    for name in services_status.keys():
        print 'service %s is %s (pid=%d)' % (name, services_status[name]['status'], services_status[name]['pid'])


def do_start_services(args, name_filter_fct=lambda x: True):
    services.log_level = args.log_level
    services.log_path = args.log_path

    services_status = services.get_current_services_status()
    for name in filter(name_filter_fct, services.names):
        if services_status[name]['status'] == 'not running':
            print 'starting service {}, log {}'.format(name, services.logfile_path(name))
            try:
                services.start(name, log_level=args.log_level, log_file_base_path=services.log_path)
                if 'pydbserver' in name:  # allow service to start up
                    _wait_for_db_ping_ok()
            except EnvironmentError as e:
                print 'Could not start service {}: {}'.format(name, e)
                sys.exit(1)


def _wait_for_db_ping_ok():
    db = pydb.pyrosetup.pydbserver()
    db_ok = False

    tries = 0
    while not db_ok and tries < 500:
        try:
            if db.ping() == 'pong':
                db_ok = True
                break
        except Pyro4.errors.CommunicationError:
            pass

        time.sleep(0.5)
        tries += 1

    return db_ok


def do_stop_services(_, name_filter_fct=lambda x: True):
    services.stop_all_ignoring_exceptions(verbose=True, name_filter_fct=name_filter_fct)


def do_restart_services(args):
    if args.web2py_only:
        do_stop_services(args, name_filter_fct=lambda x: 'web2py' in x)
        do_start_services(args, name_filter_fct=lambda x: 'web2py' in x)
    else:
        do_stop_services(args)
        do_start_services(args)


def main():
    pydb.config.read_config()
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
    parser_restart.add_argument('--web2py-only', '-w', action="store_true", default=False, help='only restart web2py')

    parser_restart.set_defaults(func=do_restart_services, debug=False, log_level='WARNING', log_path=services.log_path)

    args = parser.parse_args()

    args.func(args)


if __name__ == "__main__":
    main()


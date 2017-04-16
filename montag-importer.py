#!/usr/bin/env python2.7
# coding=utf-8

import logging
import argparse
import os

from twisted.internet import reactor, threads

import pydb.executionenvironment as executionenvironment
import pydb.pyrosetup as pyrosetup
import pydb.importer as importer
import pydb.identifier_runner as identifier_runner
import pydb.config as config
import Queue
import pydb.logconfig


logging.basicConfig(level=logging.INFO)


def determine_import_watch_folder_path(override_base_path=None):
    if override_base_path is None:
        base_path = executionenvironment.get_main_dir()
    else:
        base_path = args.basepath

    path = config.importer_watch_folder()
    if os.path.isabs(path):
        return path

    return os.path.join(base_path, path)


if __name__ == "__main__":
    pydb.config.read_config()
    pydb.logconfig.catch_twisted_log_messages()

    parser = argparse.ArgumentParser(description='Runs the bulk import server')
    # montag-services will provide the base path to all daemons - we'll just ignore it
    parser.add_argument('--basepath', '-b', dest='basepath', help='Sets the basepath for the server', action='store')
    pydb.logconfig.add_log_level_to_parser(parser)

    args = parser.parse_args()
    pydb.logconfig.set_log_level(args.loglevel)

    db_dir = executionenvironment.determine_database_directory(args.basepath)
    schema_dir = executionenvironment.get_schema_dir()

    watch_folder_path = determine_import_watch_folder_path(args.basepath)

    notification_queue = Queue.Queue()
    imp = importer.build_importer(pyrosetup.fileserver(), db_dir=db_dir, schema_dir=schema_dir,
                                  watch_folder_path=watch_folder_path, notification_queue=notification_queue,
                                  group_name=None, delete_after_import=True)

    runner_container = []

    def run_identifier_forever():
        identifier_runner_ = identifier_runner.build_identifier_runner(db_dir=db_dir, schema_dir=schema_dir)
        runner_container.append(identifier_runner_)
        identifier_runner_.process_queue_forever(notification_queue)

    threads.deferToThread(run_identifier_forever)

    watcher = importer.build_watcher(imp, watch_folder_path, reactor=reactor)
    reactor.callLater(0, watcher.start)

    reactor.addSystemEventTrigger('before', 'shutdown', lambda: runner_container[0].request_stop())

    reactor.run()


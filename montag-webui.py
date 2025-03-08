#!/usr/bin/env python3
import argparse
import os
import sys

from pydb.executionenvironment import using_py2exe
import pydb.config
import pydb.logconfig
import webui


def get_main_dir():
    if using_py2exe():
        return os.path.dirname(sys.executable)
    return os.path.dirname(sys.argv[0])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Runs the web interface')
    pydb.logconfig.add_log_level_to_parser(parser)

    args = parser.parse_args()

    pydb.logconfig.set_log_level(args.loglevel)

    pydb.config.read_config()
    os.chdir(os.path.join(get_main_dir(), 'webui'))
    webui.start_webserver()

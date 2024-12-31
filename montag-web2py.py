#!/usr/bin/env python3
import argparse
import os
import sys

from pydb.executionenvironment import using_py2exe
import pydb.config
import pydb.logconfig


def get_main_dir():
    if using_py2exe():
        return os.path.dirname(sys.executable)
    return os.path.dirname(sys.argv[0])


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Runs the web interface')
    parser.add_argument('--basepath', '-b', dest='basepath', help='Sets the basepath for the server', action='store')
    pydb.logconfig.add_log_level_to_parser(parser)
    
    args = parser.parse_args()
    
    pydb.logconfig.set_log_level(args.loglevel)

    pydb.config.read_config()
    os.chdir(os.path.join(get_main_dir(), 'web2py'))
    sys.path.append('.')
    sys.path.append('gluon')

    import web2py.gluon.widget

    # commandline for web2py to parse
    sys.argv = ['web2py.py', '-a', '12345', '-i', '0.0.0.0']
    web2py.gluon.widget.start(cron=True)

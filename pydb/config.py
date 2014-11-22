import os

import ConfigParser
import logging

logger = logging.getLogger('config')

parser = ConfigParser.SafeConfigParser()
try:
    parser.read('pydb.conf')
except Exception as e:
    logger.error('could not read config file: {}'.format(e.message))

def get_boolean_option(section, name, default):
    try:
        logger.debug('read [{}] {} '.format(section, name))
        return parser.getboolean(section, name)
    except Exception:
        logger.debug('returning default={}'.format(default))
        return default

def get_int_option(section, name, default):
    try:
        logger.debug('read [{}] {} '.format(section, name))
        return parser.getint(section, name)
    except Exception:
        logger.debug('returning default={}'.format(default))
        return default


def enable_covers():
    return get_boolean_option('common', 'enable_covers', True)

_has_ebook_convert = False


def has_ebook_convert():
    return _has_ebook_convert


def upload_rate_limit_kbytes_per_second():
    return get_int_option('comserver', 'upload_rate_limit_kbytes_per_second', 500)

def request_files_on_incoming_connection():
    return get_boolean_option('comserver', 'request_files_on_incoming_connection', True)

def comserver_port():
    return get_int_option('comserver', 'port', 1234)

def max_file_size_to_request_bytes():
    return get_int_option('comserver', 'max_file_size_to_request_bytes', 100*1000*1000)

def _load():
    global _has_ebook_convert
    if os.path.exists("/usr/bin/ebook-convert"):
        _has_ebook_convert = True


_load()
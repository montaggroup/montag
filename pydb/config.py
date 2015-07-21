import os

import ConfigParser
import logging

logger = logging.getLogger('config')

parser = None


def read_config(config_path='pydb.conf'):
    global parser
    parser = ConfigParser.SafeConfigParser()
    try:
        logger.debug('Reading {}'.format(config_path))
        parser.read(config_path)
    except (ConfigParser.NoOptionError, ConfigParser.NoSectionError, ValueError) as e:
        logger.error('could not read config file: {}'.format(e.message))


def get_boolean_option(section, name, default):
    try:
        logger.debug('read [{}] {} '.format(section, name))
        return parser.getboolean(section, name)
    except (ConfigParser.NoOptionError, ConfigParser.NoSectionError, ValueError):
        logger.debug('returning default={}'.format(default))
        return default


def get_int_option(section, name, default):
    try:
        logger.debug('read [{}] {} '.format(section, name))
        return parser.getint(section, name)
    except (ConfigParser.NoOptionError, ConfigParser.NoSectionError, ValueError):
        logger.debug('returning default={}'.format(default))
        return default


def get_string_option(section, name, default):
    try:
        logger.debug('read [{}] {} '.format(section, name))
        return parser.get(section, name)
    except (ConfigParser.NoOptionError, ConfigParser.NoSectionError, ValueError):
        logger.debug('returning default={}'.format(default))
        return default

def enable_covers():
    return get_boolean_option('common', 'enable_covers', True)

def ignore_rate_limit_in_lan():
    return get_boolean_option('common', 'ignore_rate_limit_in_lan', True)


_has_ebook_convert = None


def has_ebook_convert():
    global _has_ebook_convert

    if _has_ebook_convert is None:
        _has_ebook_convert = os.path.exists("/usr/bin/ebook-convert")

    return _has_ebook_convert


def upload_rate_limit_kbytes_per_second():
    return get_int_option('comserver', 'upload_rate_limit_kbytes_per_second', 500)


def request_files_on_incoming_connection():
    return get_boolean_option('comserver', 'request_files_on_incoming_connection', True)


def comserver_port():
    return get_int_option('comserver', 'port', 1234)


def max_file_size_to_request_bytes():
    return get_int_option('comserver', 'max_file_size_to_request_bytes', 100*1000*1000)


def enable_web_auth():
    return get_boolean_option('web', 'enable_auth', False)



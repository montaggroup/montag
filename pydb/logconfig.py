import logging

def set_log_level(loglevel_string):
    # from the python logging howto
    numeric_level = getattr(logging, loglevel_string.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: {}'.format(loglevel_string))
    logging.getLogger().setLevel(numeric_level)

def add_log_level_to_parser(parser):
    parser.add_argument('--loglevel', '-l', default="INFO", help="Log level (debug, info, warning, error, critical)")
    

def catch_twisted_log_messages():
    from twisted.python import log
    observer = log.PythonLoggingObserver()
    observer.start()


''' Logging helper.
Just import this and your logger is configured to capture
both STDOUT and STDERR alongside logging.* calls to logs/output.log
this is not intended to be a library but a helper to configure logging
import from your main.py and then use logging.getLogger(...) normally

By default this helper rotates the log files at midnight.
set SELF_ROTATE_LOGS=False if your application uses external log rotations

'''
import logging
import logging.handlers
import os
import sys
from contextlib import contextmanager

FORMATTERS = {
    'default': logging.Formatter(
        '%(asctime)s %(levelname)s (%(name)s.%(funcName)s): %(message)s'
        ),
    'lib': logging.Formatter(
        '%(asctime)s %(levelname)s: %(filename)s:%(lineno)d %(funcName)s() - %(message)s'
        ),
    'print': logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s'
        ),
    }

PATH = 'logs'
LOGNAME = 'output.log'
if not os.path.isdir(PATH):
    assert not os.path.exists(PATH)
    os.mkdir(PATH)

SELF_ROTATE_LOGS = False

HANDLER_CONFIG = {
    'filename': os.path.join(PATH, LOGNAME)
}

if SELF_ROTATE_LOGS:
    HANDLER_CONFIG['when'] = 'midnight'
    HandlerClass = logging.handlers.TimedRotatingFileHandler
else:
    HandlerClass = logging.handlers.WatchedFileHandler

DEFAULT_HANDLER = HandlerClass(**HANDLER_CONFIG)
DEFAULT_HANDLER.setFormatter(FORMATTERS['default'])
DEFAULT_HANDLER.setLevel(logging.DEBUG)

PRINTS_HANDLER = HandlerClass(**HANDLER_CONFIG)
PRINTS_HANDLER.setFormatter(FORMATTERS['print'])
PRINTS_HANDLER.setLevel(logging.DEBUG)

HANDLERS = {
    'default': DEFAULT_HANDLER,
    'prints': PRINTS_HANDLER,
}

LOGGER = logging.getLogger(__name__)
LOGGER.root.setLevel(logging.DEBUG)
LOGGER.root.addHandler(HANDLERS['default'])

class StreamToLogger:
    '''
    Fake file-like stream object that redirects writes to a logger instance.
    credit: Ferry Boender
    https://www.electricmonk.nl/log/2011/08/14/redirect-stdout-and-stderr-to-a-logger-in-python/
    '''
    def __init__(self, logger, file=None, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''
        self.file = file

    @contextmanager
    def switch_format(self):
        '''syntactic sugar to do the formatting handler replacement'''
        self.logger.root.removeHandler(HANDLERS['default'])
        self.logger.root.addHandler(HANDLERS['prints'])
        try:
            yield None
        finally:
            self.logger.root.removeHandler(HANDLERS['prints'])
            self.logger.root.addHandler(HANDLERS['default'])

    def _write(self, buf):

        for line in buf.rstrip().splitlines():
            line = line.strip()
            if not line:
                continue
            self.logger.log(self.log_level, line)
            if self.file:
                print(line, file=self.file)

    def write(self, buf):
        '''write'''
        with self.switch_format():
            self._write(buf)

    def flush(self):
        '''required for compliance'''
        pass


STDOUT_LVL = logging.DEBUG + 1

STDOUT_LOGGER = logging.getLogger('STDOUT')
logging.addLevelName(STDOUT_LVL, 'STDOUT')
STREAM_LOGGER = StreamToLogger(STDOUT_LOGGER, sys.__stdout__, STDOUT_LVL)
sys.stdout = STREAM_LOGGER

STDERR_LVL = logging.DEBUG + 2
STDERR_LOGGER = logging.getLogger('STDERR')
logging.addLevelName(STDERR_LVL, 'STDERR')
STREAM_LOGGER = StreamToLogger(STDERR_LOGGER, sys.__stderr__, STDERR_LVL)
sys.stderr = STREAM_LOGGER

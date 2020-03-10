from collections import deque
from threading import Lock

from revvy.utils.stopwatch import Stopwatch

_log_lock = Lock()


class LogLevel:
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3


levels = ('Debug', 'Info', 'Warning', 'Error')


class Logger:
    def __init__(self, buffer_size=1000):
        self._sw = Stopwatch()
        self._buffer = deque(maxlen=buffer_size)
        self.minimum_level = LogLevel.INFO
        self.on_flush = None

    def log(self, message, level=LogLevel.INFO):
        if level >= self.minimum_level:
            message = f'{self._sw.elapsed} {levels[level]}: {message}\n'
            print(message)
            self._buffer.append(message)

    def flush(self):
        if self.on_flush:
            self.on_flush(self._buffer)
            self._buffer.clear()


class LogWrapper:
    def __init__(self, logger, tag, default_log_level=LogLevel.INFO):
        self._tag = tag + ': '
        self._logger = logger
        self._default_log_level = default_log_level

    def __call__(self, message, level=None):
        message = self._tag + message
        if level is None:
            level = self._default_log_level
        self._logger.log(message, level)

    def flush(self):
        self._logger.flush()


logger = Logger()


def get_logger(tag, default_log_level=LogLevel.INFO):
    return LogWrapper(logger, tag, default_log_level)

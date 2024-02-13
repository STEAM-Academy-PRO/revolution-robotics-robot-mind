from collections import deque
import hashlib
import os
from threading import Lock
from revvy.utils.directories import WRITEABLE_DATA_DIR

from revvy.utils.stopwatch import Stopwatch
from revvy.utils.write_unique_file import create_unique_file

_log_lock = Lock()

class LogLevel:
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3


levels = (
    '\x1b[90mDebug\x1b[0m',
    '\x1b[32mInfo\x1b[0m',
    '\x1b[33mWarning\x1b[0m',
    '\x1b[31mError\x1b[0m'
)

def consistent_hash(text):
    return int(hashlib.sha1(text.encode("utf-8")).hexdigest(), 16)

color_mapping = {
    0: '\033[34m',  # Blue
    1: '\033[35m',  # Magenta
    2: '\033[36m',  # Cyan
    3: '\033[90m',  # Bright Black (Dark Gray)
    4: '\033[91m',  # Bright Red
    5: '\033[92m',  # Bright Green
    6: '\033[93m',  # Bright Yellow
    7: '\033[94m',  # Bright Blue
    8: '\033[95m',  # Bright Magenta
    9: '\033[96m'   # Bright Cyan
}

def hash_to_color(text):
    """ Simple text hasher for easy module identification on the debug logs """
    global color_mapping
    # Get a hash value using the built-in hash function
    hash_value = consistent_hash(text)

    # Map the hash value to a range suitable for ANSI color codes (0-7)
    color_code = abs(hash_value) % len(color_mapping)

    reset_color = '\033[0m'

    # Apply the color to the text
    colored_text = f"{color_mapping[color_code]}{text}{reset_color}"

    return colored_text


class BaseLogger:
    def log(self, message, level):
        pass

    def flush(self):
        pass


class Logger(BaseLogger):
    def __init__(self, buffer_size=1000):
        self._sw = Stopwatch()
        self._buffer = deque(maxlen=buffer_size)
        self.minimum_level = LogLevel.INFO
        self.branch = "dev"
        self.sw_version = "not_set"
        self.on_flush = None

    def log(self, message, level=LogLevel.INFO):
        if level >= self.minimum_level:
            message = f'[{self._sw.elapsed:.2f}] [{levels[level]}] {message}'
            print(message)
            self._buffer.append(message + '\n')


    def flush(self):
        """ Dump flashed framework version"""
        with create_unique_file(os.path.join(WRITEABLE_DATA_DIR, 'revvy_log')) as file:
            file.write(f"Framework version: {self.sw_version}-{self.branch}\n")
            try:
                file.writelines(self._buffer)
            except Exception as e:
                file.writelines('logger failed!')
        self._buffer.clear()


class LogWrapper(BaseLogger):
    def __init__(self, logger: BaseLogger, tag, default_log_level=LogLevel.INFO, min_log_level=LogLevel.DEBUG):
        self._min_log_level = min_log_level
        if isinstance(tag, str):
            self._tag = '[' + hash_to_color(tag) + '] '
        elif isinstance(tag, list):
            self._tag = ''
            for t in tag:
                self._tag += '[' + hash_to_color(t) + '] '

        self._logger = logger
        self._default_log_level = default_log_level

    def log(self, message, level=None):
        message = self._tag + message
        if level is None:
            level = self._default_log_level
        if level >= self._min_log_level:
            self._logger.log(message, level)

    def __call__(self, message, level=None):
        self.log(message, level)

    def flush(self):
        self._logger.flush()


logger = Logger()

def empty(*args):
    """ dummy """
    pass

def get_logger(tag, default_log_level=LogLevel.INFO, base=None, off=False):
    return LogWrapper(base or logger, tag, default_log_level, min_log_level=LogLevel.ERROR if off else LogLevel.DEBUG)



"""
Colorful revvy logger.
Configure it with log_config.json in the data/config directory.
@see: /docs/pi/configuration.md
"""

import os
from threading import current_thread
from typing import Optional, Union
from revvy.utils.directories import WRITEABLE_DATA_DIR
from revvy.utils.functions import read_json

from revvy.utils.stopwatch import Stopwatch


class LogLevel:
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    OFF = 4


LEVELS = (
    "\x1b[90mDebug\x1b[0m",
    "\x1b[32mInfo\x1b[0m",
    "\x1b[33mWarning\x1b[0m",
    "\x1b[31mError\x1b[0m",
)


color_mapping = (
    "\033[34m",  # Blue
    "\033[35m",  # Magenta
    "\033[36m",  # Cyan
    "\033[90m",  # Bright Black (Dark Gray)
    "\033[91m",  # Bright Red
    "\033[92m",  # Bright Green
    "\033[93m",  # Bright Yellow
    "\033[94m",  # Bright Blue
    "\033[95m",  # Bright Magenta
    "\033[96m",  # Bright Cyan
)


def hash_to_color(text: str) -> str:
    """
    Simple text hasher for easy module identification on the debug logs
    """
    # Quickly turn the string into a somewhat random, but deterministic number
    hash_value = sum(text.encode())

    # Map the hash value to a range suitable for ANSI color codes (0-7)
    color_code = hash_value % len(color_mapping)

    # Apply the color to the text
    colored_text = f"{color_mapping[color_code]}{text}\033[0m"

    return colored_text


START_TIME = Stopwatch()


class Logger:
    def __init__(
        self,
        tag: str,
        colored_tag: str,
        default_log_level=LogLevel.INFO,
        min_log_level=LogLevel.INFO,
    ):
        self._default_log_level = default_log_level
        self._min_log_level = min_log_level
        self.tag = tag
        self.colored_tag = colored_tag

    def log(self, message: str, level=None):
        """Print to log if level is higher than the minimum log level."""
        if level is None:
            level = self._default_log_level

        if level >= self._min_log_level and level < LogLevel.OFF:
            thread_name = hash_to_color(current_thread().name)

            # Print the newline ourselves.
            # This removes the possibility of racy threads to mess up the output.
            message = f"[{START_TIME.elapsed:.2f}][{LEVELS[level]}][{thread_name}]{self.colored_tag} {message}\n"
            print(message, end="")

    __call__ = log


log_config = None

""" Logging configuration.

Keys:
- enabled: dict of enabled tags
- default_log_level: default log level.
                     Logging calls without an explicit level will emit at this level.
- min_log_level: minimum log level. Logging calls with a level below this will be ignored.
"""


def get_log_config() -> dict:
    """
    Load config from data/config/log_config.json or default.
    """
    global log_config
    if log_config is None:
        # Try to load the log_config.json file
        try:
            log_config = read_json(os.path.join(WRITEABLE_DATA_DIR, "config", "log_config.json"))
        except FileNotFoundError:
            print("[WARNING] Failed to load log_config.json")
            log_config = {}

        # Merge missing keys from default
        default_log_config = {
            "modules": {},
            "min_log_level": LogLevel.INFO,
            "default_log_level": LogLevel.INFO,
        }
        log_config = {**default_log_config, **log_config}

        print("[Logger] Loaded log config:", log_config)

    return log_config


def get_logger(
    tag: Union[str, list[str]],
    default_log_level: Optional[int] = None,
    base: Optional[Logger] = None,
    logger_type=Logger,
):
    """
    Returns specific module logger.
    """
    scoped_log_config = get_log_config()

    if not isinstance(tag, list):
        tag = [tag]

    base_tag = base.tag if base else ""
    colored_tag = base.colored_tag if base else ""

    # Module or tag specific log level
    level_filter = None
    for t in tag:
        base_tag += f"[{t}]"
        if base_tag in scoped_log_config["modules"]:
            level_filter = scoped_log_config["modules"][base_tag]

        colored_tag += "[" + hash_to_color(t) + "]"

    if not isinstance(level_filter, int):
        level_filter = scoped_log_config["min_log_level"]
        if not isinstance(level_filter, int):
            level_filter = LogLevel.ERROR

    # Get default log level from config file if not provided
    if default_log_level is None:
        default_log_level = scoped_log_config["default_log_level"] or LogLevel.ERROR
        if not isinstance(default_log_level, int):
            default_log_level = LogLevel.ERROR

    return logger_type(base_tag, colored_tag, default_log_level, level_filter)

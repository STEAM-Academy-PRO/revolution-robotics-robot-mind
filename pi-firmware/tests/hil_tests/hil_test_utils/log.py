from threading import current_thread
from threading import Lock

import sys
from typing import List, Optional, Union
from revvy.utils.logger import LogLevel, hash_to_color, LEVELS
from revvy.utils.stopwatch import Stopwatch

messages = []
lock = Lock()
TEST_START_TIME = Stopwatch()


class BufferingLogger:
    def __init__(
        self,
        tag: str,
        colored_tag: str,
        default_log_level=LogLevel.INFO,
        min_log_level=LogLevel.DEBUG,
    ):
        self._default_log_level = default_log_level
        self._min_log_level = min_log_level
        self.tag = tag
        self.colored_tag = colored_tag

    def __call__(self, message: str, level=None):
        """Print to log if level is higher than the minimum log level."""
        if level is None:
            level = self._default_log_level

        if level >= self._min_log_level and level < LogLevel.OFF:
            thread_name = hash_to_color(current_thread().name)

            # Print the newline ourselves.
            # This removes the possibility of racy threads to mess up the output.
            message = f"[{TEST_START_TIME.elapsed:.2f}][{LEVELS[level]}][{thread_name}]{self.colored_tag} {message}"
            with lock:
                messages.append(message)


def install_memory_logger() -> None:
    module = sys.modules["revvy.utils.logger"]
    original_get_logger = module.get_logger

    def get_memory_logger(
        tag: Union[str, List[str]],
        default_log_level: Optional[int] = None,
        base: Optional[BufferingLogger] = None,
    ):
        return original_get_logger(tag, default_log_level, base, BufferingLogger)

    module.get_logger = get_memory_logger  # pyright: ignore

    sys.modules["revvy.utils.logger"] = module


def clear_logs() -> None:
    with lock:
        global messages
        messages.clear()
        TEST_START_TIME.reset()


def take_messages() -> List[str]:
    with lock:
        # replace with empty list and return
        global messages
        result, messages = messages, []
        return result


def ansi_colored(s, color):
    return f"\033[{color}m{s}\033[0m"


def red(s):
    return ansi_colored(s, "91")


def green(s):
    return ansi_colored(s, "92")

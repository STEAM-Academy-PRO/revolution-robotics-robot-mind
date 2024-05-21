import time


class Stopwatch:
    """Class to measure elapsed time in seconds"""

    def __init__(self) -> None:
        """Initialize and start the stopwatch"""
        self._start_time = time.time()

    def reset(self) -> None:
        """Reset elapsed time"""
        self._start_time = time.time()

    @property
    def elapsed(self) -> float:
        """Read the elapsed time in seconds"""
        return time.time() - self._start_time

import time


class Stopwatch:
    def __init__(self):
        self._start_time = time.time()

    def reset(self):
        self._start_time = time.time()

    @property
    def elapsed(self):
        return time.time() - self._start_time

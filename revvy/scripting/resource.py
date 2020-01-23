# SPDX-License-Identifier: GPL-3.0-only

from threading import Lock

from revvy.robot.ports.common import FunctionAggregator
from revvy.utils.logger import get_logger


class ResourceHandle:
    def __init__(self, resource: 'Resource'):
        self._resource = resource
        self._on_interrupted = FunctionAggregator()
        self._on_released = FunctionAggregator()
        self._is_interrupted = False

    @property
    def on_interrupted(self):
        return self._on_interrupted

    @property
    def on_released(self):
        return self._on_released

    def release(self):
        self.on_released()
        self._resource.release(self)

    def interrupt(self):
        self._is_interrupted = True
        self.on_interrupted()

    def run_uninterruptable(self, callback):
        with self._resource:
            if not self._is_interrupted:
                return callback()

    @property
    def is_interrupted(self):
        return self._is_interrupted


class Resource:
    def __init__(self, name='Resource'):
        self._lock = Lock()
        self._log = get_logger(f'Resource [{name}]')
        self._current_priority = -1
        self._active_handle = None

    def __enter__(self):
        self._lock.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._lock.__exit__(exc_type, exc_val, exc_tb)

    def reset(self):
        self._log('Reset')
        with self._lock:
            handle = self._active_handle
            self._active_handle = None

            if handle:
                self._log('Interrupting active resource handle')
                handle.interrupt()

            self._current_priority = -1

    def request(self, with_priority=0, on_taken_away=None):
        self._log(f'enter request ({with_priority})')
        with self._lock:
            if self._active_handle is None:
                self._log('no current owner')
                self._create_new_handle(with_priority, on_taken_away)
                return self._active_handle

            elif self._current_priority == with_priority:
                self._log('taking from equal prio owner')
                return self._active_handle

            elif self._current_priority > with_priority:
                self._log('taking from lower prio owner')
                self._active_handle.interrupt()
                self._create_new_handle(with_priority, on_taken_away)
                return self._active_handle

            else:
                self._log('failed to take')
                return None

    def _create_new_handle(self, with_priority, on_taken_away):
        self._current_priority = with_priority
        self._active_handle = ResourceHandle(self)
        if on_taken_away:
            self._active_handle.on_interrupted.add(on_taken_away)

    def release(self, resource_handle):
        self._log('enter release')
        with self._lock:
            if self._active_handle == resource_handle:
                self._active_handle = None
                self._current_priority = -1
                self._log('released')
            else:
                self._log('not releasing')

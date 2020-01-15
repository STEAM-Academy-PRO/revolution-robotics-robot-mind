# SPDX-License-Identifier: GPL-3.0-only

from threading import Lock

from revvy.utils.logger import get_logger


class ResourceHandle:
    def __init__(self, resource, callback=None):
        self._resource = resource
        self._callback = callback
        self._is_interrupted = False

    def release(self):
        self._resource.release(self)

    def interrupt(self):
        self._is_interrupted = True
        if self._callback:
            self._callback()

    def run_uninterruptable(self, callback):
        with self._resource._lock:
            if not self._is_interrupted:
                return callback()

    @property
    def is_interrupted(self):
        return self._is_interrupted


class Resource:
    def __init__(self, name='Resource'):
        self._lock = Lock()
        self._log = get_logger('Resource [{}]'.format(name))
        self._current_priority = -1
        self._active_handle = None

    @property
    def lock(self):
        return self._lock

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
        self._log('enter request ({})'.format(with_priority))
        with self._lock:
            if self._active_handle is None:
                self._log('no current owner')
                self._current_priority = with_priority
                self._active_handle = ResourceHandle(self, on_taken_away)
                return self._active_handle

            elif self._current_priority == with_priority:
                self._log('taking from equal prio owner')
                return self._active_handle

            elif self._current_priority > with_priority:
                self._log('taking from lower prio owner')
                self._active_handle.interrupt()
                self._current_priority = with_priority
                self._active_handle = ResourceHandle(self, on_taken_away)
                return self._active_handle

            else:
                self._log('failed to take')
                return None

    def release(self, resource_handle):
        self._log('enter release')
        with self._lock:
            if self._active_handle == resource_handle:
                self._active_handle = None
                self._current_priority = -1
                self._log('released')
            else:
                self._log('not releasing')

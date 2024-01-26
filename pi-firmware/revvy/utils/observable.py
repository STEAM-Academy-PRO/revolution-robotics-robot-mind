""" Simple observable implementation. """

import threading
from time import time

from typing import Generic, TypeVar, Callable, List


VariableType = TypeVar('VariableType')

class Observable(Generic[VariableType]):
    """ Simple Observable Implementation """
    def __init__(self, value=None, throttle_interval=0):
        self._observers = []
        self._data: VariableType = value

        # Throttling
        self._throttle_interval = throttle_interval
        self._last_update_time = 0
        self._update_pending = False

    def subscribe(self, observer: Callable):
        self._observers.append(observer)

    def unsubscribe(self, observer: Callable):
        self._observers.remove(observer)

    def notify(self):
        """ If not throttling, effects are instant. If throttling, effects are delayed. """
        if self._throttle_interval == 0:
            for observer in self._observers:
                observer(self)
        else:
            current_time = time()
            if current_time - self._last_update_time > self._throttle_interval:
                for observer in self._observers:
                    observer(self)
                self._last_update_time = current_time
                self._update_pending = False
            else:
                if not self._update_pending:
                    self._update_pending = True
                    threading.Timer(self._throttle_interval, self._check_pending_update).start()

    def _check_pending_update(self):
        if self._update_pending:
            self.notify()


    def set(self, new_data: VariableType):
        if new_data != self._data:
            # For lists or complex objects, make a deep copy
            if isinstance(new_data, list):
                self._data = new_data.deep_copy()
            else:
                self._data = new_data
            self.notify()

    def get(self):
        return self._data

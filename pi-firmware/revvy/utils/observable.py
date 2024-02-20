"""
Observable value implementation.

An observable value raises an event when its value changes.
Outside code can subscribe to these events and react to them.
"""

import copy
import threading
from time import time

from typing import Generic, TypeVar, Callable, List

from revvy.utils.emitter import SimpleEventEmitter


VariableType = TypeVar("VariableType")


class Observable(Generic[VariableType]):
    """Simple Observable Implementation"""

    def __init__(self, value=None, throttle_interval=0):
        self._on_value_changed = SimpleEventEmitter()
        self._data: VariableType = value

        # Throttling
        self._throttle_interval = throttle_interval
        self._last_update_time = 0
        self._update_pending = False

    def subscribe(self, observer: Callable):
        self._on_value_changed.add(observer)

    def unsubscribe(self, observer: Callable):
        self._on_value_changed.remove(observer)

    def notify(self):
        """If not throttling, observers are notified instantly. If throttling is enabled, events are emitted at most once per period."""
        if self._throttle_interval == 0:
            self._on_value_changed.trigger(self._data)
        else:
            current_time = time()
            since_last_emit = current_time - self._last_update_time
            if since_last_emit >= self._throttle_interval:
                self._on_value_changed.trigger(self._data)
                self._last_update_time = current_time
                self._update_pending = False
            else:
                # set up a recall for the next period, counted from the last event
                if not self._update_pending:
                    self._update_pending = True
                    timer_thread = threading.Timer(
                        self._throttle_interval - since_last_emit, self._check_pending_update
                    )
                    timer_thread.name = "ObservableThrottleTimer"
                    timer_thread.start()

    def _check_pending_update(self):
        if self._update_pending:
            self.notify()

    def set(self, new_data: VariableType):
        if new_data != self._data:
            # For lists or complex objects, make a deep copy
            if isinstance(new_data, list):
                self._data = copy.deepcopy(new_data)
            else:
                self._data = new_data
            self.notify()

    def get(self):
        return self._data


class SmoothingObservable(Observable):
    """
    When dealing with noisy data, we want to smooth it out.
    e.g. when measuring something like a battery voltage, we want to
    have stable readings, that are not toggling between two values, rather
    going just down.

    This only sends notifications, if the average of the last `smoothing_window`
    elements change.
    """

    def __init__(
        self,
        value,
        throttle_interval=0,
        window_size=10,
        precision=1,
        smoothening_function: Callable = None,
    ):
        super().__init__(value, throttle_interval)
        self._data_history = [] if not value else [value]
        self._window_size = window_size
        self._precision = precision
        self._data = value
        self._last_data = value
        self._smoothening_function = smoothening_function

    def set(self, new_data: VariableType):
        self._data_history.append(new_data)

        # If the length is larger than the window, ditch first element.
        if len(self._data_history) > self._window_size:
            self._data_history.pop(0)

        if self._smoothening_function:
            new_value = self._smoothening_function(self._data_history)
        else:
            # simple average func
            new_value = sum(self._data_history) / len(self._data_history)
            new_value = round(new_value * self._precision) / self._precision

        super().set(new_value)

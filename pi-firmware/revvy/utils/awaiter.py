from enum import Enum
from threading import Lock, Condition

from revvy.utils.emitter import SimpleEventEmitter


class WaitableValue:
    def __init__(self, default=None):
        self._value = default
        self._condition = Condition(Lock())

    def exchange_if(self, expected, new):
        """Compare and exchange. Returns the stored value, stores the new one if the stored value equals the expected"""
        with self._condition:
            if self._value == expected:
                old, self._value = self._value, new
                self._condition.notify_all()
                return old
            else:
                return self._value

    def set(self, value):
        """Update the stored value. Wake up threads waiting for a value"""
        with self._condition:
            self._value = value
            self._condition.notify_all()

    def get(self):
        """Return the current value"""
        with self._condition:
            return self._value

    def wait(self, timeout=None):
        """Wait for a value to be set()"""
        with self._condition:
            if self._condition.wait(timeout):
                return self._value
            else:
                raise TimeoutError

    def map(self, callback):
        """Perform an operation on the current value"""
        with self._condition:
            return callback(self._value)


class AwaiterState(Enum):
    """The states an awaiter can be in."""
    NONE = 0,
    CANCEL = 1,
    FINISHED = 2


class Awaiter:
    """A flag that one piece of code can set/cancel and another can wait for it to be set."""
    @classmethod
    def from_state(cls, state):
        return cls(state)

    def __init__(self, initial_state=AwaiterState.NONE):
        self._lock = Lock()
        self._signal = WaitableValue(initial_state)

        self._cancellation_callbacks = SimpleEventEmitter()
        self._completion_callbacks = SimpleEventEmitter()

    def _add_callback(self, callbacks: SimpleEventEmitter, callback, call_for_state: AwaiterState):
        def _append_callback(current_state):
            if current_state == AwaiterState.NONE:
                callbacks.add(callback)
                return False
            elif current_state == call_for_state:
                return True

        call_immediately = self._signal.map(_append_callback)

        if call_immediately:
            callback()

    def on_cancelled(self, callback):
        """Register a callback to be called when the awaiter is cancelled"""
        self._add_callback(self._cancellation_callbacks, callback, AwaiterState.CANCEL)

    def on_finished(self, callback):
        """Register a callback to be called when the awaiter has finished successfully"""
        self._add_callback(self._completion_callbacks, callback, AwaiterState.FINISHED)

    def cancel(self):
        """Cancel the pending awaiter. Does nothing if the awaiter has already finished"""
        if self._signal.exchange_if(AwaiterState.NONE, AwaiterState.CANCEL) == AwaiterState.NONE:
            self._cancellation_callbacks()

    def finish(self):
        """Mark the pending awaiter as finished."""
        if self._signal.exchange_if(AwaiterState.NONE, AwaiterState.FINISHED) == AwaiterState.NONE:
            self._completion_callbacks()

    @property
    def state(self):
        return self._signal.get()

    def wait(self, timeout=None):
        """
        Wait for the operation to finish

        @param timeout:
        @return: True if the operation was finished by calling finish(), False if cancelled or timed out
        """
        if self._signal.get() != AwaiterState.NONE:
            return True

        try:
            self._signal.wait(timeout)
            return self._signal.get() == AwaiterState.FINISHED
        except TimeoutError:
            return False

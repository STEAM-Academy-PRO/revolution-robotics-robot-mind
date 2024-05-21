from enum import Enum
from threading import Lock, Condition
from typing import Any, Callable, Generic, Optional, TypeVar

from revvy.utils.emitter import SimpleEventEmitter


T = TypeVar("T")
RV = TypeVar("RV")


class WaitableValue(Generic[T]):
    def __init__(self, initial: T):
        self._value = initial
        self._condition = Condition(Lock())

    def exchange_if(self, expected: T, new: T):
        """Compare and exchange. Returns the stored value, stores the new one if the stored value equals the expected"""
        with self._condition:
            if self._value == expected:
                old, self._value = self._value, new
                self._condition.notify_all()
                return old
            else:
                return self._value

    def set(self, value: T):
        """Update the stored value. Wake up threads waiting for a value"""
        with self._condition:
            self._value = value
            self._condition.notify_all()

    def get(self) -> T:
        """Return the current value"""
        with self._condition:
            return self._value

    def wait(self, timeout: Optional[float] = None) -> T:
        """Wait for a value to be set()"""
        with self._condition:
            if self._condition.wait(timeout):
                return self._value
            else:
                raise TimeoutError

    def map(self, callback: Callable[[T], RV]) -> RV:
        """Perform an operation on the current value"""
        with self._condition:
            return callback(self._value)


class AwaiterState(Enum):
    """The states an awaiter can be in."""

    NONE = 0
    CANCEL = 1
    FINISHED = 2


class Awaiter:
    """A flag that one piece of code can set/cancel and another can wait for it to be set."""

    def __init__(self, initial_state: AwaiterState = AwaiterState.NONE):
        self._lock = Lock()
        self._signal = WaitableValue(initial_state)

        self._cancellation_callbacks = SimpleEventEmitter()
        self._completion_callbacks = SimpleEventEmitter()

    def _add_callback(self, callbacks: SimpleEventEmitter, callback, call_for_state: AwaiterState):
        def _append_callback(current_state: AwaiterState):
            if current_state == AwaiterState.NONE:
                callbacks.add(callback)
                return False
            else:
                # if we're in an end state, trigger immediately
                return current_state == call_for_state

        call_immediately = self._signal.map(_append_callback)

        if call_immediately:
            callback()

    def on_cancelled(self, callback: Callable):
        """Register a callback to be called when the awaiter is cancelled"""
        self._add_callback(self._cancellation_callbacks, callback, AwaiterState.CANCEL)

    def on_finished(self, callback: Callable):
        """Register a callback to be called when the awaiter has finished successfully"""
        self._add_callback(self._completion_callbacks, callback, AwaiterState.FINISHED)

    def _complete(self, state: AwaiterState) -> bool:
        return self._signal.exchange_if(AwaiterState.NONE, state) == AwaiterState.NONE

    def cancel(self) -> None:
        """Cancel the pending awaiter. Does nothing if the awaiter has already finished"""
        if self._complete(AwaiterState.CANCEL):
            self._cancellation_callbacks.trigger()

    def finish(self) -> None:
        """Mark the pending awaiter as finished."""
        if self._complete(AwaiterState.FINISHED):
            self._completion_callbacks.trigger()

    @property
    def state(self) -> AwaiterState:
        return self._signal.get()

    def wait(self, timeout: Optional[float] = None):
        """
        Wait for the operation to finish

        @param timeout:
        @return: True if the operation was finished by calling finish(), False if cancelled or timed out
        """
        if self._signal.get() != AwaiterState.NONE:
            return self._signal.get() == AwaiterState.FINISHED

        try:
            self._signal.wait(timeout)
            return self._signal.get() == AwaiterState.FINISHED
        except TimeoutError:
            return False

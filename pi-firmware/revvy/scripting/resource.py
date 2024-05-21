import abc
from threading import Lock
from typing import Any, Callable, Optional, Union

from revvy.utils.emitter import SimpleEventEmitter
from revvy.utils.logger import get_logger, LogLevel


class BaseHandle(abc.ABC):
    @abc.abstractmethod
    def __enter__(self) -> "BaseHandle": ...

    @abc.abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb) -> None: ...

    @abc.abstractmethod
    def __bool__(self) -> bool: ...

    @abc.abstractmethod
    def interrupt(self) -> None: ...

    @abc.abstractmethod
    def release(self) -> None: ...

    @abc.abstractmethod
    def run_uninterruptable(
        self, callback
    ) -> Optional[Any]: ...  # todo: return type of the callback


class NullHandle(BaseHandle):
    def __enter__(self) -> BaseHandle:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        pass

    def __bool__(self) -> bool:
        return False

    def interrupt(self) -> None:
        pass

    def release(self) -> None:
        pass

    def run_uninterruptable(self, callback) -> Optional[Any]:
        pass


null_handle = NullHandle()


class ResourceHandle(BaseHandle):
    def __init__(self, resource: "Resource"):
        self._resource = resource
        self._on_interrupted = SimpleEventEmitter()
        self._on_released = SimpleEventEmitter()
        self._is_interrupted = False

    def __enter__(self) -> BaseHandle:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.release()

    def __bool__(self) -> bool:
        return True

    @property
    def on_interrupted(self) -> SimpleEventEmitter:
        return self._on_interrupted

    @property
    def on_released(self) -> SimpleEventEmitter:
        return self._on_released

    def release(self) -> None:
        self.on_released.trigger()
        self._resource.release(self)

    def interrupt(self) -> None:
        self._is_interrupted = True
        self.on_interrupted.trigger()

    def run_uninterruptable(self, callback) -> Optional[Any]:
        with self._resource:
            if not self._is_interrupted:
                return callback()

    @property
    def is_interrupted(self) -> bool:
        return self._is_interrupted


class Resource:
    """
    A global token that symbolizes some shared hardware element, implementing priority-based access.

    Resources need to be bound to scripts before they can be accessed.
    """

    def __init__(self, name: Union[str, list[str]] = "Resource"):
        self._lock = Lock()
        self._log = get_logger(name, LogLevel.DEBUG)
        self._current_priority = -1
        self._active_handle = null_handle

    def __enter__(self) -> bool:
        return self._lock.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._lock.__exit__(exc_type, exc_val, exc_tb)

    def reset(self) -> None:
        # self._log('Reset')
        with self._lock:
            handle, self._active_handle = self._active_handle, null_handle

            if handle:
                self._log("Interrupting active resource handle")
                handle.interrupt()

            self._current_priority = -1

    def request(
        self, with_priority=0, on_taken_away: Optional[Callable[[], None]] = None
    ) -> BaseHandle:
        with self._lock:
            if not self._active_handle:
                self._log(f"create handle for priority {with_priority}")
                self._create_new_handle(with_priority, on_taken_away)
                return self._active_handle

            elif self._current_priority >= with_priority:
                self._log(
                    f"taking from lower prio owner (request: {with_priority}, holder: {self._current_priority})"
                )
                self._active_handle.interrupt()
                self._create_new_handle(with_priority, on_taken_away)
                return self._active_handle

            else:
                self._log(
                    f"failed to take resource (request: {with_priority}, holder: {self._current_priority})"
                )
                return null_handle

    def _create_new_handle(self, with_priority, on_taken_away) -> None:
        self._current_priority = with_priority
        self._active_handle = ResourceHandle(self)
        if on_taken_away:
            self._active_handle.on_interrupted.add(on_taken_away)

    def release(self, resource_handle) -> None:
        with self._lock:
            if self._active_handle == resource_handle:
                self._active_handle = null_handle
                self._current_priority = -1
                self._log("released")
            else:
                self._log("failed to release, not owned")

from enum import Enum
import time
from threading import Event, Thread, Lock, RLock
import traceback
from typing import Callable, Optional
from revvy.utils.error_reporter import RobotErrorType, revvy_error_handler
from revvy.utils.emitter import SimpleEventEmitter

from revvy.utils.logger import LogLevel, get_logger


class ThreadWrapperState(Enum):
    STOPPED = 0
    STARTING = 1
    RUNNING = 2
    STOPPING = 3
    EXITED = 4


class EmitterWithDefaultHandler(SimpleEventEmitter):
    """Event emitter that has a default handler that is called when no other handler is present."""

    def __init__(self, default_handler: Callable):
        super().__init__()
        self._default_handler = default_handler

    def trigger(self, *args, **kwargs) -> None:
        if self.is_empty():
            self._default_handler(*args, **kwargs)
        else:
            super().trigger(*args, **kwargs)


class ThreadWrapper:
    """
    Helper class to enable stopping/restarting threads from the outside
    Threads are not automatically stopped (as it is not possible), but a stop request can be read
    using the context object that is passed to the thread function.
    """

    def __init__(self, func, name: str = "WorkerThread"):
        self._log = get_logger(["ThreadWrapper", name])
        self._log("created", LogLevel.DEBUG)
        self._lock = Lock()  # lock used to ensure internal consistency
        # prevent concurrent access. RLock so that callbacks may restart the thread
        self._interface_lock = RLock()
        self._func = func
        self._stopped_callbacks = SimpleEventEmitter()
        self._stop_requested_callbacks = SimpleEventEmitter()
        self._error_callbacks = EmitterWithDefaultHandler(self._report_error)
        self._pause_flag = Event()
        self._pause_flag.set()  # when set, the code can run
        self._control = Event()  # used to wake up thread function when it is stopped
        self._stop_event = Event()  # used to signal thread function that it should stop
        # caller can wait for thread to stop after calling stop()
        self._thread_stopped_event = Event()
        self._thread_stopped_event.set()
        # caller can wait for the thread function to start running
        self._thread_running_event = Event()
        self._state = ThreadWrapperState.STOPPED
        self._is_exiting = False
        self._thread = Thread(target=self._thread_func, args=(), name=name)
        self._thread.start()

    def _report_error(self, exc: Exception) -> None:
        formatted = traceback.format_exc()
        self._log(f"Unhandled: {formatted}", LogLevel.ERROR)
        revvy_error_handler.report_error(RobotErrorType.SYSTEM, formatted)

    def _wait_for_start(self) -> bool:
        """Wait for the thread to be started. Returns False if the thread is exiting."""
        self._control.wait()
        self._control.clear()

        return self._state == ThreadWrapperState.STARTING

    def _thread_func(self) -> None:
        try:
            ctx = ThreadContext(self)
            while self._wait_for_start():
                try:
                    self._enter_started()
                    self._func(ctx)
                except InterruptedError:
                    self._log("interrupted")
                except Exception as e:
                    self._error_callbacks.trigger(e)

                finally:
                    self._enter_stopped()
        finally:
            self._state = ThreadWrapperState.EXITED

    def _enter_started(self) -> None:
        with self._lock:
            self._stop_event.clear()
            self._state = ThreadWrapperState.RUNNING
            self._thread_running_event.set()
        self._log("thread started", LogLevel.DEBUG)

    def _enter_stopped(self) -> None:
        self._log("stopped", LogLevel.DEBUG)
        with self._lock:
            self._state = ThreadWrapperState.STOPPED
            self._thread_running_event.clear()
            self._thread_stopped_event.set()
            self._log("call stopped callbacks", LogLevel.DEBUG)
            self._stopped_callbacks.trigger()

    @property
    def state(self) -> ThreadWrapperState:
        return self._state

    @property
    def is_running(self) -> bool:
        return self._thread_running_event.is_set()

    def wait_for_running(self, timeout: Optional[float] = None) -> bool:
        return self._thread_running_event.wait(timeout)

    def start(self) -> None:
        """Starts the thread if it is not already running. Does nothing if the thread is already running."""
        assert self._state != ThreadWrapperState.EXITED, "thread has already exited"
        assert not self._is_exiting, "can not start an exiting thread"

        with self._interface_lock:
            with self._lock:
                if self._state != ThreadWrapperState.STOPPED:
                    return

            if self._is_exiting:
                return
            self._log("starting", LogLevel.DEBUG)
            self._thread_stopped_event.clear()
            self._state = ThreadWrapperState.STARTING
            self._control.set()

    def stop(self) -> Event:
        """If the thread is already stopped or stopping, does nothing."""

        # It is possible that the wrapped thread calls `stop` while an other thread calls `exit`.
        # To avoid a deadlock, we try to acquire the lock without blocking, and if
        # we can't, we check if the lock is held by `exit`.
        acquired = self._interface_lock.acquire(blocking=False)
        try:
            if not acquired and self._is_exiting:
                return self._thread_stopped_event

            return self.do_stop()
        finally:
            if acquired:
                self._interface_lock.release()

    def do_stop(self) -> Event:
        with self._interface_lock:
            if self._state not in [
                ThreadWrapperState.STARTING,
                ThreadWrapperState.RUNNING,
            ]:
                self._log(
                    f"Stop called but thread is not in a running state. Currently in state: {self._state}"
                )
            else:
                self._log("stopping")

                if self._state == ThreadWrapperState.STARTING:
                    self._log("startup is in progress, wait for thread to start running")
                    self._thread_running_event.wait()

                with self._lock:
                    if self._state == ThreadWrapperState.RUNNING:
                        self._log("request stop", LogLevel.DEBUG)

                        self._state = ThreadWrapperState.STOPPING
                        self._stop_event.set()
                        self.resume_thread()
                        call_callbacks = True
                    else:
                        call_callbacks = False

                if call_callbacks:
                    self._log("call stop requested callbacks", LogLevel.DEBUG)
                    self._stop_requested_callbacks.trigger()
                    self._log("stop requested callbacks finished", LogLevel.DEBUG)

            return self._thread_stopped_event

    def exit(self) -> None:
        with self._interface_lock:
            self._log("exiting", LogLevel.DEBUG)
            self._is_exiting = True

            evt = self.do_stop()
            self._log("waiting for stop event to be set", LogLevel.DEBUG)
            evt.wait()

            # wake up thread in case it is waiting to be started
            # thread will see STOPPED state and will exit
            self._control.set()

            self._log("exited", LogLevel.DEBUG)

    def on_stopped(self, callback: Callable):
        self._stopped_callbacks.add(callback)

    def on_error(self, callback: Callable[[Exception], None]):
        self._error_callbacks.add(callback)

    def on_stop_requested(self, callback: Callable):
        if self._state == ThreadWrapperState.STOPPING:
            callback()
        else:
            self._stop_requested_callbacks.add(callback)

    def pause_thread(self) -> None:
        # pause essentially means that a script calling `sleep` will not wake up. We insert a bunch
        # of `sleep` calls in the blockly to create the illusion of parallel execution, so
        # this may be good enough for now?
        self._log("pause thread")
        self._pause_flag.clear()

    def resume_thread(self) -> None:
        self._log("resume thread")
        self._pause_flag.set()


class ThreadContext:
    """Context object passed to the thread function that runs in the thread wrapper."""

    def __init__(self, thread: ThreadWrapper):
        self._thread = thread

    def stop(self) -> Event:
        return self._thread.stop()

    def on_stopped(self, callback: Callable) -> None:
        self._thread.on_stop_requested(callback)

    def sleep(self, s: float):
        """A custom sleep function that can be interrupted by stop()"""
        if self._thread._stop_event.wait(s):
            raise InterruptedError
        self._thread._pause_flag.wait()

    @property
    def stop_requested(self) -> bool:
        return self._thread._stop_event.is_set()


def periodic(fn: Callable, period: float, name: str = "PeriodicThread") -> ThreadWrapper:
    """
    Call fn periodically

    :param fn: the function to run
    :param period: period time in seconds
    :param name: optional name to prefix the thread log messages
    :return: the created thread object
    """

    def _call_periodically(ctx: ThreadContext):
        _next_call = time.time()
        while not ctx.stop_requested:
            fn()

            _next_call += period
            now = time.time()
            diff = _next_call - now
            if diff > 0:
                time.sleep(diff)
            else:
                # period was missed, let's restart
                _next_call = now

    return ThreadWrapper(_call_periodically, name)

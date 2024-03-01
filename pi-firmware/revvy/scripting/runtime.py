""" Handles blockly and analog script running lifecycle """

from enum import Enum
import time

from typing import TYPE_CHECKING, Optional
from revvy.utils.emitter import Emitter

# To have types, use this to avoid circular dependencies.
if TYPE_CHECKING:
    from revvy.robot.robot import Robot
    from revvy.robot_config import RobotConfig

from revvy.utils.logger import get_logger
from revvy.utils.thread_wrapper import ThreadContext, ThreadWrapper
from revvy.scripting.robot_interface import RobotWrapper


class ScriptEvent(Enum):
    STOP = 0
    START = 1
    ERROR = 2


class ScriptDescriptor:
    name: str
    runnable: callable
    priority: int
    source: str
    ref_id: str

    def __init__(self, name, runnable, priority, source="", ref_id=None):
        self.name = name
        self.runnable = runnable
        self.priority = priority
        self.source = source
        self.ref_id = ref_id


class TimeWrapper:
    def __init__(self, ctx: ThreadContext):
        self.time = time.time
        self.sleep = ctx.sleep


class ScriptHandle(Emitter[ScriptEvent]):
    """Creates a controller from a script descirptor"""

    def _prevent_incorrect_sleep(self, _: float):
        # The script is not running, so calling its sleep() is an error.
        self.log("Error: default sleep called")
        raise Exception("Script not running")

    def __init__(
        self, owner: "ScriptManager", descriptor: ScriptDescriptor, name, global_variables: dict
    ):
        super().__init__()
        self._owner = owner
        self._globals = global_variables.copy()
        self._inputs = {}
        self.name = name
        self._runnable = descriptor.runnable
        self.descriptor = descriptor
        self.sleep = self._prevent_incorrect_sleep
        self._thread = ThreadWrapper(self._run, name)
        self.log = get_logger(["Script", name])
        self.stop = self._thread.stop
        self.cleanup = self._thread.exit
        self.on_stopped = self._thread.on_stopped
        self.on_stopping = self._thread.on_stop_requested
        self.pause = self._thread.pause_thread
        self.resume = self._thread.resume_thread

        self.on_stopped(self.reset_variables)
        self.on_stopped(lambda: self.trigger(ScriptEvent.STOP))

        self._thread.on_error(self._on_error)

        # TODO: this isn't needed if everything is typed right, we can remove it later
        assert callable(self._runnable)

        self.log("Created")

    def _on_error(self, error):
        self.trigger(ScriptEvent.ERROR, error)

    @property
    def is_stop_requested(self):
        return self._thread.state in [ThreadWrapper.STOPPING, ThreadWrapper.STOPPED]

    @property
    def is_running(self):
        return self._thread.is_running

    def assign(self, name, value):
        self._globals[name] = value

    def _run(self, ctx: ThreadContext):
        try:
            # script control interface
            def _terminate():
                self.stop()
                raise InterruptedError

            # adding new methods to the context, that we may use from blockly-generated code
            ctx.terminate = _terminate  # pyright: ignore
            ctx.terminate_all = lambda: self._owner.stop_all_scripts(False)  # pyright: ignore

            self.sleep = ctx.sleep
            self.log("Starting script")
            self.trigger(ScriptEvent.START)
            self._runnable(Control=ctx, ctx=ctx, time=TimeWrapper(ctx), **self._inputs)
        except InterruptedError:
            self.log("Interrupted")
            raise
        finally:
            # restore to release reference on context
            self.log("Script finished")
            self.sleep = self._prevent_incorrect_sleep

    def reset_variables(self, *args):
        if "list_slots" in self._globals:
            for var in self._globals["list_slots"]:
                self.log(f"resetting_variable: {var}")
                var.reset_value()

    def start(self, **kwargs):
        if not kwargs:
            self._inputs = self._globals
        else:
            self._inputs = {**self._globals, **kwargs}
        return self._thread.start()


class ScriptManager:
    def __init__(self, robot: "Robot"):
        self._robot = robot
        self._globals = {}
        self._scripts: dict[str, ScriptHandle] = {}
        self._log = get_logger("ScriptManager")

    def reset(self):
        self.stop_all_scripts()
        for script in self._scripts.values():
            script.cleanup()

        self._globals.clear()
        self._scripts.clear()

        self._log("stop all scripts and reset state")

    def assign(self, name, value):
        self._globals[name] = value
        for script in self._scripts.values():
            script.assign(name, value)

    def add_script(
        self,
        script: ScriptDescriptor,
        # tests don't pass a config, which is weird and probably wrong
        config: Optional["RobotConfig"] = None,
        robot_wrapper_class=RobotWrapper,
    ):
        # TODO: This is a not a good place here: we should not need to check if a script
        # is running, when trying to override it, lifecycle should prevent this from
        # ever happening.
        if script.name in self._scripts:
            self._log(f"Stopping {script.name} before overriding")
            self._scripts[script.name].cleanup()

        self._log(f"New script: {script.name}")
        script_handle = ScriptHandle(self, script, script.name, self._globals)
        try:
            # Note: Due to dependency injection, this is wrapped out.
            # FIXME the lint ignore shouldn't be there. Fix tests.
            interface = robot_wrapper_class(
                script_handle, self._robot, config, self._robot.resources, script.priority  # type: ignore tests pass a None and a mock wrapper
            )
            script_handle.on_stopping(interface.release_resources)
            script_handle.on_stopped(interface.release_resources)
            script_handle.assign("robot", interface)
            self._scripts[script.name] = script_handle

            return script_handle
        except Exception:
            script_handle.cleanup()
            raise

    def __getitem__(self, name):
        return self._scripts[name]

    def stop_all_scripts(self, wait=True):
        events = []
        for script in self._scripts.values():
            events.append(script.stop())

        if wait:
            for event in events:
                event.wait()

    def start_all_scripts(self):
        for script in self._scripts.values():
            script.start()

    def pause_all_scripts(self):
        for script in self._scripts.values():
            script.pause()

    def resume_all_scripts(self):
        for script in self._scripts.values():
            script.resume()

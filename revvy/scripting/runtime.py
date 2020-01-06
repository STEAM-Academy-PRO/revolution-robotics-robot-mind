# SPDX-License-Identifier: GPL-3.0-only

from revvy.scripting.robot_interface import RobotInterface
import time

from revvy.utils.logger import Logger
from revvy.utils.thread_wrapper import ThreadContext, ThreadWrapper


class TimeWrapper:
    def __init__(self, ctx: ThreadContext):
        self.time = time.time
        self.sleep = ctx.sleep


class ScriptHandle:
    def __init__(self, owner, script, name, global_variables: dict):
        self._owner = owner
        self._globals = dict(global_variables)
        self._thread = ThreadWrapper(self._run, 'ScriptThread: {}'.format(name))
        self._inputs = {}
        self._logger = Logger('Script: {}'.format(name))

        self.stop = self._thread.stop
        self.cleanup = self._thread.exit
        self.on_stopped = self._thread.on_stopped
        self.sleep = lambda s: None

        if callable(script):
            self.log('Created from callable')
            self._runnable = script
        elif type(script) is str:
            self.log('Created from string')
            self._runnable = lambda x: exec(script, x)
        else:
            raise AssertionError

    def log(self, message):
        self._logger(message)

    @property
    def is_stop_requested(self):
        return self._thread.stopping

    @property
    def is_running(self):
        return self._thread.is_running

    def assign(self, name, value):
        self._globals[name] = value

    def _run(self, ctx):
        try:
            # script control interface
            def _terminate():
                self.stop()
                raise InterruptedError

            ctx.terminate = _terminate
            ctx.terminate_all = self._owner.stop_all_scripts

            self.sleep = ctx.sleep
            self._runnable({
                **self._globals,
                **self._inputs,
                'Control': ctx,
                'ctx': ctx,
                'time': TimeWrapper(ctx)
            })
        finally:
            self._thread_ctx = None
            self.sleep = lambda s: None

    def start(self, variables=None):
        if variables is not None:
            self._inputs = variables
        else:
            self._inputs.clear()
        return self._thread.start()


class ScriptManager:
    def __init__(self, robot):
        self._robot = robot
        self._globals = {}
        self._scripts = {}
        self._log = Logger('ScriptManager')

    def reset(self):
        self._log('stopping scripts')
        for script in self._scripts:
            self._scripts[script].cleanup()

        self._log('resetting state')
        self._globals.clear()
        self._scripts.clear()

    def assign(self, name, value):
        self._globals[name] = value
        for script in self._scripts:
            self._scripts[script].assign(name, value)

    def add_script(self, name, script, priority=0):
        if name in self._scripts:
            self._log('Stopping {} before overriding'.format(name))
            self._scripts[name].cleanup()

        self._log('New script: {}'.format(name))
        script = ScriptHandle(self, script, name, self._globals)
        try:
            robot = self._robot
            script.assign('robot', RobotInterface(script, robot.robot, robot.config, robot.resources, priority))
            self._scripts[name] = script
        except Exception:
            script.cleanup()
            raise

    def __getitem__(self, name):
        return self._scripts[name]

    def stop_all_scripts(self):
        for script in self._scripts:
            self._scripts[script].stop()

# SPDX-License-Identifier: GPL-3.0-only
import time
import copy

from collections import namedtuple
from threading import Event

from revvy.utils.activation import EdgeDetector
from revvy.utils.stopwatch import Stopwatch
from revvy.utils.thread_wrapper import ThreadWrapper, ThreadContext
from revvy.utils.logger import get_logger

RemoteControllerCommand = namedtuple('RemoteControllerCommand', ['analog', 'buttons', 'background_command'])

AUTONOMOUS_MODE_REQUEST_NONE   = 0
AUTONOMOUS_MODE_REQUEST_STOP   = 1
AUTONOMOUS_MODE_REQUEST_START  = 2
AUTONOMOUS_MODE_REQUEST_PAUSE  = 3
AUTONOMOUS_MODE_REQUEST_RESUME = 4

class AutonomousModeRequest:
    def __init__(self):
        self.__state = AUTONOMOUS_MODE_REQUEST_NONE

    def set_start_request(self):
        self.__state = AUTONOMOUS_MODE_REQUEST_START

    def set_stop_request(self):
        self.__state = AUTONOMOUS_MODE_REQUEST_STOP

    def set_pause_request(self):
        self.__state = AUTONOMOUS_MODE_REQUEST_PAUSE

    def set_resume_request(self):
        self.__state = AUTONOMOUS_MODE_REQUEST_RESUME

    def is_start_pending(self):
        return self.__state == AUTONOMOUS_MODE_REQUEST_START

    def is_stop_pending(self):
        return self.__state == AUTONOMOUS_MODE_REQUEST_STOP

    def is_pause_pending(self):
        return self.__state == AUTONOMOUS_MODE_REQUEST_PAUSE

    def is_resume_pending(self):
        return self.__state == AUTONOMOUS_MODE_REQUEST_RESUME

    def clear_pending(self):
        self.__state = AUTONOMOUS_MODE_REQUEST_NONE


BACKGROUND_CONTROL_STATE_STOPPED = 1
BACKGROUND_CONTROL_STATE_RUNNING = 2
BACKGROUND_CONTROL_STATE_PAUSED  = 3

class BackgroundControlState:
    def __init__(self):
        self.__state = BACKGROUND_CONTROL_STATE_STOPPED

    def __state_to_str(self):
        if self.__state == BACKGROUND_CONTROL_STATE_STOPPED:
            return 'bg_state:stopped'
        if self.__state == BACKGROUND_CONTROL_STATE_RUNNING:
            return 'bg_state:running'
        if self.__state == BACKGROUND_CONTROL_STATE_PAUSED:
            return 'bg_state:paused'
        return 'bg_state:undefined'

    def __str__(self):
        return self.__state_to_str()

    def __repr__(self):
        return self.__state_to_str()

    def set_stopped(self):
        self.__state = BACKGROUND_CONTROL_STATE_STOPPED

    def set_paused(self):
        self.__state = BACKGROUND_CONTROL_STATE_PAUSED

    def set_running(self):
        self.__state = BACKGROUND_CONTROL_STATE_RUNNING

    def get_numeric(self):
        return self.__state


class RemoteController:
    def __init__(self):
        self._background_control_state = BackgroundControlState()
        self.__autonomous_mode_rq = AutonomousModeRequest()
        self._log = get_logger('RemoteController')

        self._analogActions = []  # ([channel], callback) pairs
        self._analogStates = []  # the last analog values, used to compare if a callback needs to be fired
        self._buttonHandlers = [EdgeDetector() for _ in range(32)]
        self._buttonActions = [None] * 32  # callbacks to be fired if a button gets pressed

        for handler in self._buttonHandlers:
            handler.handle(1)

        self._processing = False
        self._processing_time = 0.0
        self._previous_time = None

        # Joystick mode opposed to autonomous mode
        # Difference matters for the processing_time (aka the 'global timer'),
        # as for in simple joystick mode, processing time should not start until
        # the user presses something on a joystick, therefore we have to
        # know the difference in code
        self._joystick_mode = False

    def on_joystick_action(self):
        # This is a one shot action to detect first joystick input
        # over one entire contoller (play) session
        if self._joystick_mode:
            return

        self._joystick_mode = True
        self._processing = True
        self._previous_time = time.time()

    def reset(self):
        self._log('RemoteController: reset')
        self._analogActions.clear()
        self._analogStates.clear()

        self._buttonActions = [None] * 32
        self._processing = False
        self._processing_time = 0.0
        self._background_control_state.set_stopped()
        self._previous_time = None
        self._joystick_mode = False

        for handler in self._buttonHandlers:
            handler.handle(1)

    def process_bg_command(self, command):
        if not command:
            return

        commands = BleProto.Autonomous.Command
        command_functions = {
            commands.START : self.on_bg_command_start,
            commands.PAUSE : self.on_bg_command_pause,
            commands.RESUME: self.on_bg_command_resume,
            commands.RESET : self.on_bg_command_reset
        }
        if command in command_functions:
            command_functions[command]()

    def process_analog_command(self, analog_cmd):
        if analog_cmd == self._analogStates:
            return

        previous_analog_states = self._analogStates
        self._analogStates = analog_cmd
        for channels, action in self._analogActions:
            try:
                try:
                    changed = any(previous_analog_states[x] != analog_cmd[x] for x in channels)
                except IndexError:
                    changed = True

                if changed:
                    action([analog_cmd[x] for x in channels])
            except IndexError:
                # looks like an action was registered for an analog channel that we didn't receive
                self._log(f'Skip analog handler for channels {", ".join(map(str, channels))}')

    def process_button_command(self, button_cmd):
        for handler, button, action in zip(self._buttonHandlers, button_cmd, self._buttonActions):
            pressed = handler.handle(button)
            if pressed == 1 and action:
                # noinspection PyCallingNonCallable
                action()

    def process_msg(self, msg):
        self.process_bg_command(msg.background_command)
        self.process_analog_command(msg.analog)
        self.process_button_command(msg.buttons)

    def on_button_pressed(self, button, action: callable):
        self._buttonActions[button] = action

    def on_analog_values(self, channels, action):
        self._analogActions.append((channels, action))

    def on_bg_command_start(self):
        self._background_control_state.set_running()
        self.__autonomous_mode_rq.set_start_request()
        if not self._joystick_mode:
            self._processing = True
            self._processing_time = 0.0
            self._previous_time = time.time()

    def on_bg_command_reset(self):
        self._background_control_state.set_stopped()
        self.__autonomous_mode_rq.set_stop_request()
        self._processing = False
        self._processing_time = 0.0
        self._previous_time = None

    def on_bg_command_pause(self):
        self._background_control_state.set_paused()
        self.__autonomous_mode_rq.set_pause_request()
        self.timer_increment()
        self._processing = False
        self._previous_time = None

    def on_bg_command_resume(self):
        self._background_control_state.set_running()
        self.__autonomous_mode_rq.set_resume_request()
        self._processing = True
        self._previous_time = time.time()

    def timer_increment(self):
        if self._processing:
            current_time = time.time()
            self._processing_time += current_time - self._previous_time
            self._previous_time = current_time

    @property
    def processing_time(self):
        return round(self._processing_time, 2)

    @property
    def background_control_state(self):
        return self._background_control_state

    def fetch_autonomous_requests(self):
        result = copy.copy(self.__autonomous_mode_rq)
        self.__autonomous_mode_rq.clear_pending()
        return result


class BleProto:
    class Autonomous:
        class Command:
            START  = 10
            PAUSE  = 11
            RESUME = 12
            RESET  = 13


class RemoteControllerScheduler:

    first_message_timeout = 5
    message_max_period = 1

    def __init__(self, rc: RemoteController):
        self._controller = rc
        self._data_ready_event = Event()
        self._controller_detected_callback = None
        self._controller_lost_callback = None
        self._message = None
        self._log = get_logger('RemoteControllerScheduler')

    def data_ready(self, message: RemoteControllerCommand):
        self._message = message
        self._data_ready_event.set()


    def _wait_for_message(self, ctx, wait_time):
        timeout = not self._data_ready_event.wait(wait_time)
        self._data_ready_event.clear()

        return not (timeout or ctx.stop_requested)

    def handle_controller(self, ctx: ThreadContext):
        self._log('Waiting for controller')

        self._data_ready_event.clear()

        ctx.on_stopped(self._data_ready_event.set)

        # wait for first message
        stopwatch = Stopwatch()
        if self._wait_for_message(ctx, self.first_message_timeout):
            self._log(f"Time to first message: {stopwatch.elapsed}s")
            if self._controller_detected_callback:
                self._controller_detected_callback()

            self._controller.process_msg(self._message)

            # wait for the other messages
            while self._wait_for_message(ctx, self.message_max_period):
                self._controller.process_msg(self._message)

        if not ctx.stop_requested:
            if self._controller_lost_callback:
                self._controller_lost_callback()

        # reset here, controller was lost or stopped
        self._controller.reset()
        self._log('exited')

    def on_controller_detected(self, callback: callable):
        self._log('Register controller found handler')
        self._controller_detected_callback = callback

    def on_controller_lost(self, callback: callable):
        self._log('Register controller lost handler')
        self._controller_lost_callback = callback

def create_remote_controller_thread(rcs: RemoteControllerScheduler):
    return ThreadWrapper(rcs.handle_controller, "RemoteControllerThread")

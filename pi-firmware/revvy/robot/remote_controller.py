import time
import copy

from collections import namedtuple
from threading import Event

from revvy.utils.activation import EdgeDetector
from revvy.utils.stopwatch import Stopwatch
from revvy.utils.thread_wrapper import ThreadWrapper, ThreadContext
from revvy.utils.logger import get_logger

RemoteControllerCommand = namedtuple('RemoteControllerCommand', ['analog', 'buttons', 'background_command', 'next_deadline'])

log = get_logger('RemoteController')

class BleAutonomousCmd:
    START  = 10
    PAUSE  = 11
    RESUME = 12
    RESET  = 13


class AutonomousModeRequest:
    NONE   = 0
    STOP   = 1
    START  = 2
    PAUSE  = 3
    RESUME = 4

    def __init__(self):
        self.__state = AutonomousModeRequest.NONE

    def set_start_request(self):
        self.__state = AutonomousModeRequest.START

    def set_stop_request(self):
        self.__state = AutonomousModeRequest.STOP

    def set_pause_request(self):
        self.__state = AutonomousModeRequest.PAUSE

    def set_resume_request(self):
        self.__state = AutonomousModeRequest.RESUME

    def is_start_pending(self):
        return self.__state == AutonomousModeRequest.START

    def is_stop_pending(self):
        return self.__state == AutonomousModeRequest.STOP

    def is_pause_pending(self):
        return self.__state == AutonomousModeRequest.PAUSE

    def is_resume_pending(self):
        return self.__state == AutonomousModeRequest.RESUME

    def clear_pending(self):
        self.__state = AutonomousModeRequest.NONE


class BackgroundControlState:
    STOPPED = 1
    RUNNING = 2
    PAUSED  = 3

    def __init__(self):
        self.__state = BackgroundControlState.STOPPED

    def __state_to_str(self):
        if self.__state == BackgroundControlState.STOPPED:
            return 'bg_state:stopped'
        if self.__state == BackgroundControlState.RUNNING:
            return 'bg_state:running'
        if self.__state == BackgroundControlState.PAUSED:
            return 'bg_state:paused'
        return 'bg_state:undefined'

    def __str__(self):
        return self.__state_to_str()

    def __repr__(self):
        return self.__state_to_str()

    def set_stopped(self):
        self.__state = BackgroundControlState.STOPPED

    def set_paused(self):
        self.__state = BackgroundControlState.PAUSED

    def set_running(self):
        self.__state = BackgroundControlState.RUNNING

    def get_numeric(self):
        return self.__state


class RemoteController:
    def __init__(self):
        self._background_control_state = BackgroundControlState()
        self._control_button_pressed = AutonomousModeRequest()

        self._analogActions = []  # ([channel], callback) pairs
        self._analogStates = []  # the last analog values, used to compare if a callback needs to be fired
        self._buttonHandlers = [EdgeDetector() for _ in range(32)]
        self._is_action_running = [False] * 32  # Track if a button bound program is running.
        self._buttonActions = [None] * 32  # callbacks to be fired if a button gets pressed

        self.reset_button_states()

        self._processing = False
        self._processing_time = 0.0
        self._previous_time = None

        # Joystick mode opposed to autonomous mode
        # Difference matters for the processing_time (aka the 'global timer'),
        # as for in simple joystick mode, processing time should not start until
        # the user presses something on a joystick, therefore we have to
        # know the difference in code
        self._joystick_mode = False
        self.__next_deadline = MESSAGE_MAX_PERIOD

    def reset_button_states(self):
        # Button handlers used for edge detection, initialize them with value
        for handler in self._buttonHandlers:
            # Originally, this was 1, but there is a bug that the first button presses
            # did not run the code after entering to play mode.
            handler.detect_change(0)


    def get_next_deadline(self):
        return self.__next_deadline

    def on_joystick_action(self):
        # This is a one shot action to detect first joystick input
        # over one entire controller (play) session
        if self._joystick_mode:
            return
        log('Joystick mode ON')
        self._joystick_mode = True
        self._processing = True
        self._previous_time = time.time()

    def reset_background_control_state(self):
        self._background_control_state.set_stopped()

    def reset(self):
        log('RemoteController: reset')
        self._analogActions.clear()
        self._analogStates.clear()

        self._buttonActions = [None] * 32
        self._processing = False
        self._processing_time = 0.0
        self._background_control_state.set_stopped()
        self._previous_time = None
        self._joystick_mode = False


    def process_background_command(self, cmd):
        if cmd == BleAutonomousCmd.START:
            log(f'start background program: {cmd}')
            self.start_background_functions()
        elif cmd == BleAutonomousCmd.PAUSE:
            self.pause_background_functions()
        elif cmd == BleAutonomousCmd.RESUME:
            self.resume_background_functions()
        elif cmd == BleAutonomousCmd.RESET:
            self.reset_background_functions()

    def process_analog_command(self, analog_cmd):
        """
            Handles joystick movement and triggers change (action)
            if any of the values changed
        """
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
                log(f'Skip analog handler for channels {", ".join(map(str, channels))}')

    def run_button_script(self, button_cmd):
        """
            On the controller user binds blockly programs to the buttons.
            Here we iterate over the handlers and the button states, and if the button is pressed
            run the program.
            We also send a message about it being started.
        """

        for handler, button, buttonAction in zip(self._buttonHandlers, button_cmd, self._buttonActions):
            pressed = handler.detect_change(button)
            if pressed == 1 and buttonAction:
                log(f'starting program: {button} {handler}')
                # noinspection PyCallingNonCallable
                buttonAction()

    def process_control_message(self, msg):
        """
            The app sends regular (<100ms) control messages.
            This function handles: analog inputs, button bound script running and background programs
            It also updates the next_deadline - to notice if the session disconnects,
            and switch the motors off.
        """
        self.process_background_command(msg.background_command)
        self.process_analog_command(msg.analog)
        self.run_button_script(msg.buttons)
        if msg.next_deadline is not None:
            self.__next_deadline = msg.next_deadline

    def set_on_button_pressed(self, button, action: callable):
        self._buttonActions[button] = action

    def on_analog_values(self, channels, action):
        self._analogActions.append((channels, action))

    def start_background_functions(self):
        self._background_control_state.set_running()
        self._control_button_pressed.set_start_request()
        if not self._joystick_mode:
            self._processing = True
            self._processing_time = 0.0
            self._previous_time = time.time()

    def reset_background_functions(self):
        self._background_control_state.set_stopped()
        self._control_button_pressed.set_stop_request()
        self._processing = False
        self._processing_time = 0.0
        self._previous_time = None

    def pause_background_functions(self):
        self._background_control_state.set_paused()
        self._control_button_pressed.set_pause_request()
        self.timer_increment()
        self._processing = False
        self._previous_time = None

    def resume_background_functions(self):
        self._background_control_state.set_running()
        self._control_button_pressed.set_resume_request()
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
        return self._background_control_state.get_numeric()

    def fetch_autonomous_requests(self):
        result = copy.copy(self._control_button_pressed)
        self._control_button_pressed.clear_pending()
        return result


FIRST_MESSAGE_TIMEOUT = 5
MESSAGE_MAX_PERIOD = 1


log = get_logger('RemoteControllerScheduler')

class RemoteControllerScheduler:
    def __init__(self, rc: RemoteController):
        self._controller = rc
        self._data_ready_event = Event()
        self._controller_detected_callback = None
        self._controller_lost_callback = None
        self._message = None

    def periodic_control_message_handler(self, message: RemoteControllerCommand):
        self._message = message
        self._data_ready_event.set()

    def _wait_for_message(self, ctx, wait_time):
        # Wait time is in the middle of integration, we have to have default
        # behavior for mobile versions that will have zeroes in deadline field
        # Previous expectation was 200ms
        wait_time_default = 0.2
        timeout_sec = wait_time if wait_time else wait_time_default
        timeout = not self._data_ready_event.wait(timeout_sec)
        self._data_ready_event.clear()

        return not (timeout or ctx.stop_requested)

    def handle_controller(self, ctx: ThreadContext):
        log('Waiting for controller')

        self._data_ready_event.clear()

        ctx.on_stopped(self._data_ready_event.set)

        # wait for first message
        stopwatch = Stopwatch()
        if self._wait_for_message(ctx, FIRST_MESSAGE_TIMEOUT):
            log(f"Time to first message: {stopwatch.elapsed}s")
            if self._controller_detected_callback:
                self._controller_detected_callback()

            self._controller.process_control_message(self._message)

            # wait for the other messages
            while self._wait_for_message(ctx, self._controller.get_next_deadline()):
                self._controller.process_control_message(self._message)

        if not ctx.stop_requested:
            if self._controller_lost_callback:
                self._controller_lost_callback()

        # reset here, controller was lost or stopped
        self._controller.reset()
        log('exited')

    def on_controller_detected(self, callback: callable):
        # log('Register controller found handler')
        self._controller_detected_callback = callback

    def on_controller_lost(self, callback: callable):
        # log('Register controller lost handler')
        self._controller_lost_callback = callback

def create_remote_controller_thread(rcs: RemoteControllerScheduler):
    return ThreadWrapper(rcs.handle_controller, "RemoteControllerThread")

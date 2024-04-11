from dataclasses import dataclass
from enum import Enum
import time

from threading import Event
import traceback
from typing import Callable, NamedTuple, Optional, Tuple
from revvy.bluetooth.data_types import BackgroundControlState, TimerData
from revvy.scripting.runtime import ScriptHandle
from revvy.utils import error_reporter

from revvy.utils.stopwatch import Stopwatch
from revvy.utils.thread_wrapper import ThreadWrapper, ThreadContext
from revvy.utils.logger import LogLevel, get_logger


log = get_logger("RemoteController")


class BleAutonomousCmd(Enum):
    NONE = 0
    START = 10
    PAUSE = 11
    RESUME = 12
    RESET = 13


class RemoteControllerCommand(NamedTuple):
    """Raw message coming through the ble interface"""

    analog: bytearray
    buttons: list[bool]
    background_command: BleAutonomousCmd
    next_deadline: Optional[int]


EMPTY_REMOTE_CONTROLLER_COMMAND = RemoteControllerCommand(
    analog=bytearray(),
    buttons=[False] * 32,
    background_command=BleAutonomousCmd.NONE,
    next_deadline=None,
)


class AutonomousModeRequest(Enum):
    NONE = 0
    STOP = 1
    START = 2
    PAUSE = 3
    RESUME = 4


@dataclass
class ButtonHandler:
    id: int
    script: ScriptHandle
    last_button_value: bool
    last_press_stopped_it: bool


AnalogAction = Tuple[list[int], ScriptHandle]
""" ([channel], callback) pairs"""


class RemoteController:

    def __init__(self) -> None:
        self._background_control_state = BackgroundControlState.STOPPED
        self._control_button_pressed = AutonomousModeRequest.NONE

        self._analogActions: list[AnalogAction] = []
        # the last analog values, used to compare if a callback needs to be fired
        self._analogStates = bytearray()

        self._button_handlers: list[ButtonHandler] = []

        self._global_timer_running = False
        self._global_timer = 0.0
        self._previous_global_timer_value = 0.0

        self._joystick_mode_detected = False
        """Whether user input was detected.

        Difference matters for the processing_time (aka the 'global timer'),
        as for in simple joystick mode, processing time should not start until
        the user presses something on a joystick, therefore we have to
        know the difference in code
        """

        # Wait time is in the middle of integration, we have to have default
        # behavior for mobile versions that will have zeroes in deadline field
        # Previous expectation was 200ms
        self.next_message_deadline = DEFAULT_MESSAGE_DEADLINE

    def reset_background_control_state(self) -> None:
        self._background_control_state = BackgroundControlState.STOPPED

    def reset(self) -> None:
        self._analogActions.clear()
        self._analogStates.clear()
        self._button_handlers.clear()

        self._global_timer_running = False
        self._global_timer = 0.0
        self._background_control_state = BackgroundControlState.STOPPED
        self._previous_global_timer_value = None
        self._joystick_mode_detected = False

    def process_background_command(self, cmd: BleAutonomousCmd):
        # TODO: (╯°□°）╯︵ ┻━┻
        # Processes the autonomous command, sets up a bunch of state and flags
        # The actual autonomous command is then handled by the MCU_TICK event, which is nonsense.
        # Additionally, the state should not be equal to the last command immediately.
        if cmd == BleAutonomousCmd.START:
            log(f"start background program: {cmd}")
            self._background_control_state = BackgroundControlState.RUNNING
            self._control_button_pressed = AutonomousModeRequest.START
            if not self._joystick_mode_detected:
                self._global_timer_running = True
                self._global_timer = 0.0
                self._previous_global_timer_value = time.time()
        elif cmd == BleAutonomousCmd.PAUSE:
            self._background_control_state = BackgroundControlState.PAUSED
            self._control_button_pressed = AutonomousModeRequest.PAUSE
            self.timer_increment()
            self._global_timer_running = False
            self._previous_global_timer_value = None
        elif cmd == BleAutonomousCmd.RESUME:
            self._background_control_state = BackgroundControlState.RUNNING
            self._control_button_pressed = AutonomousModeRequest.RESUME
            self._global_timer_running = True
            self._previous_global_timer_value = time.time()
        elif cmd == BleAutonomousCmd.RESET:
            self._background_control_state = BackgroundControlState.STOPPED
            self._control_button_pressed = AutonomousModeRequest.STOP
            self._global_timer_running = False
            self._global_timer = 0.0
            self._previous_global_timer_value = None

    def process_analog_command(self, analog_cmd: bytearray):
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
                    action.start(channels=[analog_cmd[x] for x in channels])
            except IndexError:
                # looks like an action was registered for an analog channel that we didn't receive
                log(f'Skip analog handler for channels {", ".join(map(str, channels))}')

    def run_button_script(self, button_pressed_list: list[bool]):
        """
        On the controller user binds blockly programs to the buttons.
        Here we iterate over the handlers and the button states, and if the button is pressed
        run the program.
        We also send a message about it being started.
        """

        for button in self._button_handlers:
            button_is_pressed = button_pressed_list[button.id]
            is_button_pressed_change = button.last_button_value != button_is_pressed
            button.last_button_value = button_is_pressed

            if is_button_pressed_change:
                button.last_press_stopped_it = False

            if button_is_pressed:
                if button.script.is_running:
                    # Button pressed, script is running, there are two options:
                    # if the user tapped the button and did not release it
                    # OR
                    # if the edge detector detects change again, it means that
                    # the user let it go and tapped again, which means thy means
                    # to stop it from running.

                    if is_button_pressed_change:
                        # Pushed the second time, STOP it!
                        log(f"stopping: {button.script.name}")
                        button.script.stop()
                        button.last_press_stopped_it = True
                    else:
                        # Just keeps on pushing.
                        pass
                else:
                    # If the user is holding the button, restart the program
                    if not button.last_press_stopped_it:
                        # it's not running, we need to start it!
                        log(f"starting program: {button.script.name}")
                        button.script.start()
                    else:
                        # The user is holding the button but that button press stopped the last run.
                        pass

    def process_control_message(self, msg: RemoteControllerCommand):
        """
        The app sends regular (<100ms) control messages.
        This function handles: analog inputs, button bound script running and background programs
        It also updates the next_deadline - to notice if the session disconnects,
        and switch the motors off.
        """
        self.process_background_command(msg.background_command)
        self.process_analog_command(msg.analog)
        self.run_button_script(msg.buttons)
        if msg.next_deadline is None or msg.next_deadline < DEFAULT_MESSAGE_DEADLINE:
            self.next_message_deadline = DEFAULT_MESSAGE_DEADLINE
        else:
            self.next_message_deadline = msg.next_deadline

        # Global timer needs to be started only once.
        # Check outside of the function to avoid the function call overhead
        if not self._joystick_mode_detected:
            # First user input action triggers global timer
            self.start_timer_on_interaction(msg)

    def start_timer_on_interaction(self, msg: RemoteControllerCommand):
        # Currently hardcoded for the joystick X and Y middle position.
        # FIXME: generalize if we support more input methods
        joystick_xy_action = msg.analog[0] != 127 or msg.analog[1] != 127
        joystick_button_action = any(msg.buttons)

        if joystick_xy_action or joystick_button_action:
            # This is a one shot action to detect first joystick input
            # over one entire controller (play) session
            log("Joystick mode ON")
            self._joystick_mode_detected = True
            self._global_timer_running = True
            self._previous_global_timer_value = time.time()

    def link_button_to_runner(self, button_id, script_handle: ScriptHandle):
        log(f"registering callbacks for Button: {button_id}")
        log(script_handle.descriptor.source, LogLevel.DEBUG)
        self._button_handlers.append(
            ButtonHandler(
                id=button_id,
                script=script_handle,
                last_button_value=False,
                last_press_stopped_it=False,
            )
        )

    def on_analog_values(self, channels, action: ScriptHandle) -> None:
        self._analogActions.append((channels, action))

    def timer_increment(self) -> None:
        if self._global_timer_running:
            current_time = time.time()
            self._global_timer += current_time - self._previous_global_timer_value
            self._previous_global_timer_value = current_time

    @property
    def processing_time(self) -> TimerData:
        return TimerData(self._global_timer)

    @property
    def background_control_state(self) -> BackgroundControlState:
        return self._background_control_state

    def take_autonomous_requests(self) -> AutonomousModeRequest:
        result = self._control_button_pressed
        self._control_button_pressed = AutonomousModeRequest.NONE
        return result


FIRST_MESSAGE_TIMEOUT = 5
DEFAULT_MESSAGE_DEADLINE = 1


class RemoteControllerScheduler:
    """Receive remote controller control messages, and pass them to the controller.

    This class is responsible for handling message timeouts and controller detection/loss."""

    def __init__(self, rc: RemoteController):
        self._controller = rc
        self._data_ready_event = Event()
        self._controller_detected_callback = None
        self._controller_lost_callback = None
        self._message = EMPTY_REMOTE_CONTROLLER_COMMAND

    def periodic_control_message_handler(self, message: RemoteControllerCommand):
        """This function is called by the ble interface to pass the received control message."""

        # We want to block the BLE thread as little as possible. Therefore in this function we
        # only swap the message and signal the controller thread that new data is available.
        # The controller thread is waiting for the event to be set in `_wait_for_message`.
        # Blocking the BLE thread may cause the Raspberry Pi Zero W2 to drop connection and the
        # BLE interface to stop working.
        self._message = message
        self._data_ready_event.set()

    def _wait_for_message(
        self, ctx: ThreadContext, timeout_sec: float
    ) -> Optional[RemoteControllerCommand]:
        """Wait for the next message from the controller, or a stop request.

        If this function returns None, the remote controller thread will stop. This can happen
        in two ways:
        - a stop request was received, which is mostly interesting during development and testing
        - the timeout was reached, and we assume that the remote controller disconnected
        """
        timeout = not self._data_ready_event.wait(timeout_sec)
        self._data_ready_event.clear()

        if timeout or ctx.stop_requested:
            return None

        # swap out the message with an empty one
        # if we wanted to be 100% correct here, we should use a 1-element queue. However,
        # the swap is atomic, so in the worst case we just miss messages for a short time.
        message, self._message = self._message, EMPTY_REMOTE_CONTROLLER_COMMAND

        return message

    def handle_controller(self, ctx: ThreadContext):
        try:
            log("Waiting for controller")

            self._data_ready_event.clear()

            ctx.on_stopped(self._data_ready_event.set)

            # wait for first message
            stopwatch = Stopwatch()
            message = self._wait_for_message(ctx, FIRST_MESSAGE_TIMEOUT)
            if message is not None:
                log(f"Time to first message: {stopwatch.elapsed}s")
                if self._controller_detected_callback:
                    self._controller_detected_callback()

                # process message and wait for the next one
                while message is not None:
                    self._controller.process_control_message(message)
                    message = self._wait_for_message(ctx, self._controller.next_message_deadline)

            if not ctx.stop_requested:
                log("Controller lost due to timeout!", LogLevel.WARNING)
                if self._controller_lost_callback:
                    self._controller_lost_callback()

            # reset here, controller was lost or stopped
            self._controller.reset()
            log("exited")
        except Exception as e:
            error_reporter.revvy_error_handler.report_error(
                error_reporter.RobotErrorType.SYSTEM, traceback.format_exc()
            )
            log(str(e), LogLevel.ERROR)
            log(traceback.format_exc(), LogLevel.ERROR)

    def on_controller_detected(self, callback: Callable):
        # log('Register controller found handler')
        self._controller_detected_callback = callback

    def on_controller_lost(self, callback: Callable):
        # log('Register controller lost handler')
        self._controller_lost_callback = callback


def create_remote_controller_thread(rcs: RemoteControllerScheduler):
    return ThreadWrapper(rcs.handle_controller, "RemoteControllerThread")

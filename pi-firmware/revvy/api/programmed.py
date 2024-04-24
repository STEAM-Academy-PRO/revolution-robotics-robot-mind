import copy
from threading import Event, Lock, Thread, Timer
import time
from typing import Optional
from revvy.robot.remote_controller import BleAutonomousCmd, RemoteControllerCommand
from revvy.robot_config import RobotConfig
from revvy.robot_manager import RevvyStatusCode, RobotManager
from revvy.utils.logger import LogLevel, get_logger


class ProgrammedRobotController:
    def __init__(self, robot_manager: RobotManager):
        self.log = get_logger("ProgrammedRobotController")
        self.robot_manager = robot_manager
        self.robot_manager.needs_interrupting = False
        self.message = RemoteControllerCommand(
            analog=bytearray([0] * 6),
            buttons=[False] * 32,
            background_command=BleAutonomousCmd.NONE,
            next_deadline=1,
        )
        self.lock = Lock()
        self.timeout: Optional[Timer] = None
        # We clear this event when updating controller input. We then wait for this event to
        # become set to know that the controller thread has processed the input.
        self.message_updated = Event()
        self.exit = False

    def __enter__(self) -> "ProgrammedRobotController":
        self.thread = Thread(target=self._control_thread, name="ProgrammedRobotController")
        self.thread.start()
        self.robot_manager.robot_start()
        return self

    def _control_thread(self) -> None:
        while not self.exit:
            with self.lock:
                message = copy.deepcopy(self.message)
                self.message_updated.set()
            self.robot_manager.handle_periodic_control_message(message)
            time.sleep(0.1)
        self.log("Exiting control thread")

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.log("Stopping programmed robot controller")
        if self.timeout:
            self.timeout.cancel()
            self.timeout = None

        self.exit = True
        self.thread.join()
        self.robot_manager._scripts.stop_all_scripts(True)
        self.robot_manager.robot_stop()
        self.log("Stopped programmed robot controller")
        self.robot_manager.exit(RevvyStatusCode.OK)

    def _on_input_changed(self) -> None:
        self.message_updated.clear()

    def _wait_for_input_processed(self) -> None:
        self.message_updated.wait()

    def with_timeout(self, timeout: float):
        def _on_timeout() -> None:
            self.timeout = None
            self.log("Test scenario timed out", LogLevel.ERROR)
            self.robot_manager._scripts.stop_all_scripts(False)
            self.robot_manager.exit(RevvyStatusCode.ERROR)

        self.timeout = Timer(timeout, _on_timeout)
        self.timeout.start()

    def wait_for_scripts_to_end(self) -> None:
        any_running = True
        while any_running:
            any_running = False
            for script in self.robot_manager._scripts._scripts.values():
                if script.is_running:
                    any_running = True
            if any_running:
                time.sleep(0.1)

    # Raw input control

    def set_button_value(self, button: int, value: bool):
        with self.lock:
            self.message.buttons[button] = value
            self._on_input_changed()
        self._wait_for_input_processed()

    def set_analog_value(self, channel: int, value: int):
        assert value >= 0 and value <= 255

        with self.lock:
            self.message.analog[channel] = value
            self._on_input_changed()
        self._wait_for_input_processed()

    # Higher-level input control

    def configure(self, config: RobotConfig):
        self.robot_manager.robot_configure(config)

    def hold_button(self, button: int):
        self.set_button_value(button, True)

    def release_button(self, button: int):
        self.set_button_value(button, False)

    def press_button(self, button: int):
        self.log(f"Pressing button {button}")
        self.hold_button(button)
        self.release_button(button)

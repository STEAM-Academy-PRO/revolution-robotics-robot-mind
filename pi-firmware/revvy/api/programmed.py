import copy
from threading import Lock, Thread
import time
from revvy.robot.remote_controller import RemoteControllerCommand
from revvy.robot_config import RobotConfig
from revvy.robot_manager import RevvyStatusCode, RobotManager
from revvy.utils.logger import get_logger


class ProgrammedRobotController:
    def __init__(self, robot_manager: RobotManager):
        self.log = get_logger("ProgrammedRobotController")
        self.robot_manager = robot_manager
        self.robot_manager.needs_interrupting = False
        self.message = RemoteControllerCommand(
            analog=bytearray([0] * 6),
            buttons=bytearray([0] * 32),
            background_command=None,
            next_deadline=1,
        )
        self.lock = Lock()
        self.exit = False

    def __enter__(self) -> "ProgrammedRobotController":
        self.thread = Thread(target=self._control_thread, name="ProgrammedRobotController")
        self.thread.start()
        self.robot_manager.robot_start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.log("Stopping programmed robot controller")
        self.exit = True
        self.thread.join()
        self.robot_manager._scripts.stop_all_scripts(True)
        self.robot_manager.robot_stop()
        self.log("Stopped programmed robot controller")
        self.robot_manager.exit(RevvyStatusCode.OK)

    def configure(self, config: RobotConfig):
        self.robot_manager.robot_configure(config)

    def hold_button(self, button: int):
        with self.lock:
            self.message.buttons[button] = 1

    def release_button(self, button: int):
        with self.lock:
            self.message.buttons[button] = 0

    def press_button(self, button: int):
        self.hold_button(button)
        time.sleep(0.5)
        self.release_button(button)

    def _control_thread(self) -> None:
        while not self.exit:
            with self.lock:
                message = copy.deepcopy(self.message)
            self.robot_manager.handle_periodic_control_message(message)
            time.sleep(0.1)
        self.log("Exiting control thread")

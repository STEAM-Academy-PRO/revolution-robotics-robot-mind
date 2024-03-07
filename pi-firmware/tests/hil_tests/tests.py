import time
from revvy.utils.logger import Logger
from tests.hil_tests.hil_test_utils.runner import run_test_scenarios

from revvy.api.programmed import ProgrammedRobotController
from revvy.robot.robot_events import RobotEvent
from revvy.robot_config import RobotConfig

from revvy.robot_manager import RevvyStatusCode
from revvy.utils.functions import b64_encode_str


def can_play_sound(log: Logger, controller: ProgrammedRobotController):
    """A test case that configures a script to play a sound when a remote controller button is pressed."""

    def fail_on_script_error(*e) -> None:
        # In this test, if we encounter an error, let's just stop and exit
        controller.robot_manager.exit(RevvyStatusCode.ERROR)

    controller.robot_manager.on(RobotEvent.ERROR, fail_on_script_error)

    config = RobotConfig()
    config.process_script(
        {
            "assignments": {"buttons": [{"id": 1, "priority": 0}]},
            "pythonCode": b64_encode_str("""robot.play_tune("yee_haw")"""),
        },
        0,
    )

    controller.configure(config)

    log("Trying to play sound")
    controller.press_button(1)


def can_stop_script_with_long_sleep(log: Logger, controller: ProgrammedRobotController):
    """A test case that configures a script to sleep for a long time. We then stop the script by pressing a button."""

    def fail_on_script_error(*e) -> None:
        # In this test, if we encounter an error, let's just stop and exit
        controller.robot_manager.exit(RevvyStatusCode.ERROR)

    controller.robot_manager.on(RobotEvent.ERROR, fail_on_script_error)

    config = RobotConfig()
    config.process_script(
        {
            "assignments": {"buttons": [{"id": 1, "priority": 0}]},
            "pythonCode": b64_encode_str("""time.sleep(10000)"""),
        },
        0,
    )

    controller.configure(config)

    log("Start script")
    controller.press_button(1)

    time.sleep(0.2)

    log("Stop script")
    controller.press_button(1)


def test_motor_for_i2c_bug(log: Logger, controller: ProgrammedRobotController):
    # I'm using this test locally to test a non-deterministic I2C bug.
    def fail_on_script_error(*e) -> None:
        # In this test, if we encounter an error, let's just stop and exit
        controller.robot_manager.exit(RevvyStatusCode.ERROR)

    controller.robot_manager.on(RobotEvent.ERROR, fail_on_script_error)

    controller.robot_manager.robot._robot_control.test_motor_on_port(6, 60, 10)


if __name__ == "__main__":
    run_test_scenarios([can_play_sound, can_stop_script_with_long_sleep, test_motor_for_i2c_bug])

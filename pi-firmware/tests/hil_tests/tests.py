#!/usr/bin/python3

from revvy.utils.logger import Logger
from tests.hil_tests.hil_test_utils.runner import run_test_scenarios

from revvy.api.programmed import ProgrammedRobotController
from revvy.robot.robot_events import RobotEvent
from revvy.robot_config import RobotConfig

from revvy.robot_manager import RevvyStatusCode
from revvy.utils.functions import b64_encode_str


def can_play_sound(log: Logger, controller: ProgrammedRobotController):
    """A demo script that plays a sound when a button is pressed."""
    config = RobotConfig()

    def fail_on_script_error(*e) -> None:
        # In this test, if we encounter an error, let's just stop and exit
        controller.robot_manager.exit(RevvyStatusCode.ERROR)

    controller.robot_manager.on(RobotEvent.ERROR, fail_on_script_error)

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


if __name__ == "__main__":
    run_test_scenarios([can_play_sound])

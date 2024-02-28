#!/usr/bin/python3

from logging import Logger
import sys
from typing import Callable
from revvy.api.programmed import ProgrammedRobotController
from revvy.firmware_updater import update_firmware_if_needed
from revvy.robot.robot_events import RobotEvent
from revvy.robot_config import RobotConfig

from revvy.robot_manager import RobotManager, RevvyStatusCode
from revvy.utils.functions import b64_encode_str

from revvy.utils.logger import get_logger
from revvy.utils.directories import CURRENT_INSTALLATION_PATH

# Load the error reporter and init the singleton that'll catch system errors.
# noinspection unused-import
from revvy.utils.error_reporter import revvy_error_handler

log = get_logger("TestRunner")

# TODO: overwrite get_logger to capture log output into memory


def test_scenario(log: Logger, controller: ProgrammedRobotController):
    """A demo script that plays a sound when a button is pressed."""
    config = RobotConfig()

    def fail_on_script_error(*e):
        # In this test, if we encounter an error, let's just stop and exit
        controller.robot_manager.exit(RevvyStatusCode.ERROR)

    controller.robot_manager.on(RobotEvent.ERROR, fail_on_script_error)

    config.process_script(
        {
            "assignments": {"buttons": [{"id": 1, "priority": 0}]},
            "pythonCode": b64_encode_str("""robot.play_tne("yee_haw")"""),
        },
        0,
    )

    controller.configure(config)

    log("Trying to play sound")
    controller.press_button(1)


def run_scenario(scenario: Callable[[ProgrammedRobotController], None]) -> bool:
    """Runs a new test scenario"""
    log = get_logger(f"{scenario.__name__}")

    robot_manager = RobotManager()

    try:
        with ProgrammedRobotController(robot_manager) as controller:
            log("Running")
            scenario(log, controller)
    finally:
        result = robot_manager.wait_for_exit()
        if result == RevvyStatusCode.OK:
            log("Finished successfully")
        else:
            pass
        log(f"Finished with error: {result}")


if __name__ == "__main__":
    revvy_error_handler.register_uncaught_exception_handler()

    log(f"pack: {CURRENT_INSTALLATION_PATH}")
    log(f"file: {__file__}")

    # Make sure we run tests with the latest firmware
    if not update_firmware_if_needed():
        log("Revvy not started because the robot has no functional firmware")
        # exiting with integrity error forces the loader to try a previous package
        sys.exit(RevvyStatusCode.INTEGRITY_ERROR)

    # List test scenarios here
    scenarios = [test_scenario]
    failed = []
    for scenario in scenarios:
        if not run_scenario(scenario):
            failed.append(scenario.__name__)

    if failed:
        log(f"Failed scenarios: {failed}")
        sys.exit(1)

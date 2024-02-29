#!/usr/bin/python3

import traceback
from revvy.utils.logger import LogLevel, get_logger, Logger
from tests.hil_test_utils.log import install_memory_logger, take_messages, red, green, clear_logs

# Grab a logger factory before we overwrite the function
get_printing_logger = get_logger
install_memory_logger()

import sys
from typing import Callable
from revvy.api.programmed import ProgrammedRobotController
from revvy.firmware_updater import update_firmware_if_needed
from revvy.robot.robot_events import RobotEvent
from revvy.robot_config import RobotConfig

from revvy.robot_manager import RobotManager, RevvyStatusCode
from revvy.utils.functions import b64_encode_str

from revvy.utils.directories import CURRENT_INSTALLATION_PATH

# Load the error reporter and init the singleton that'll catch system errors.
# noinspection unused-import
from revvy.utils.error_reporter import revvy_error_handler


def test_failing_scenario(log: Logger, controller: ProgrammedRobotController):
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
            "pythonCode": b64_encode_str("""robot.play_tune("yee_haw")"""),
        },
        0,
    )

    controller.configure(config)

    log("Trying to play sound")
    controller.press_button(1)


def run_scenario(scenario: Callable[[Logger, ProgrammedRobotController], None]) -> bool:
    """Runs a new test scenario"""
    clear_logs()
    log = get_logger(f"{scenario.__name__}")

    old_exc_hook = revvy_error_handler.register_uncaught_exception_handler()
    robot_manager = RobotManager()

    try:
        with ProgrammedRobotController(robot_manager) as controller:
            scenario(log, controller)
    finally:
        result = robot_manager.wait_for_exit()
        sys.excepthook = old_exc_hook
        return result == RevvyStatusCode.OK


if __name__ == "__main__":
    log = get_printing_logger("TestRunner")

    log(f"pack: {CURRENT_INSTALLATION_PATH}")
    log(f"file: {__file__}")

    try:
        # Make sure we run tests with the latest firmware
        if not update_firmware_if_needed():
            log("Revvy not started because the robot has no functional firmware")
            # exiting with integrity error forces the loader to try a previous package
            sys.exit(RevvyStatusCode.INTEGRITY_ERROR)
    finally:
        # bit of a hack, but the updater uses memory logger and we want to see its messages
        # if it fails
        for message in take_messages():
            print(message)

    # List test scenarios here
    scenarios = [test_failing_scenario, test_scenario]
    failed = 0
    total = 0
    try:
        for scenario in scenarios:
            success = False
            try:
                total += 1
                log(f"Running scenario: {scenario.__name__}")
                success = run_scenario(scenario)
            except Exception as e:
                log(red(f"Error running scenario: {scenario.__name__}"), LogLevel.ERROR)
                log(f"Exception: {e}", LogLevel.ERROR)
                log(traceback.format_exc(), LogLevel.DEBUG)
            finally:
                if success:
                    log(green(f"{scenario.__name__}: ok"))
                else:
                    failed += 1
                    log(red(f"{scenario.__name__}: failed"))
                    log(f"=== Start logs of '{scenario.__name__}' ===")
                    for message in take_messages():
                        print(f"{scenario.__name__}: {message}")
                    log(f"=== End logs of '{scenario.__name__}' ===")
    finally:
        if failed > 0:
            log(f"{failed}/{total} scenarios failed")
            sys.exit(1)

import traceback
from revvy.hardware_dependent.rrrc_transport_i2c import RevvyTransportI2C
from revvy.mcu.rrrc_control import RevvyTransportBase
from revvy.utils.logger import LogLevel, get_logger, Logger
from tests.hil_tests.hil_test_utils.log import (
    install_memory_logger,
    take_messages,
    red,
    green,
    clear_logs,
)

# Grab a logger factory before we overwrite the function
get_printing_logger = get_logger
install_memory_logger()

import sys
from typing import Callable, List
from revvy.api.programmed import ProgrammedRobotController
from revvy.firmware_updater import update_firmware_if_needed

from revvy.robot_manager import RobotManager, RevvyStatusCode

from revvy.utils.directories import CURRENT_INSTALLATION_PATH

# Load the error reporter and init the singleton that'll catch system errors.
# noinspection unused-import
from revvy.utils.error_reporter import revvy_error_handler


def run_scenario(
    scenario: Callable[[Logger, ProgrammedRobotController], None], interface: RevvyTransportBase
) -> bool:
    """Runs a new test scenario"""
    clear_logs()
    log = get_logger(f"{scenario.__name__}")

    old_exc_hook = sys.excepthook
    revvy_error_handler.register_uncaught_exception_handler()
    robot_manager = RobotManager(interface)

    try:
        with ProgrammedRobotController(robot_manager) as controller:
            scenario(log, controller)
    except Exception as e:
        log(f"Exception: {e}", LogLevel.ERROR)
        log(traceback.format_exc(), LogLevel.DEBUG)
        robot_manager.exit(RevvyStatusCode.ERROR)
        raise e
    finally:
        result = robot_manager.wait_for_exit()
        sys.excepthook = old_exc_hook
        return result == RevvyStatusCode.OK


def run_test_scenarios(scenarios: List[Callable[[Logger, ProgrammedRobotController], None]]):
    log = get_printing_logger("TestRunner")

    log(f"pack: {CURRENT_INSTALLATION_PATH}")
    log(f"file: {__file__}")

    interface = RevvyTransportI2C(bus=1)

    try:
        # Make sure we run tests with the latest firmware
        if not update_firmware_if_needed(interface):
            log("Revvy not started because the robot has no functional firmware")
            # exiting with integrity error forces the loader to try a previous package
            sys.exit(RevvyStatusCode.INTEGRITY_ERROR)
    except Exception as e:
        # bit of a hack, but the updater uses memory logger and we want to see its messages
        # if it fails
        log(red(f"Error updating firmware: {e}"), LogLevel.ERROR)
        log(traceback.format_exc(), LogLevel.DEBUG)
        for message in take_messages():
            print(message)
        sys.exit(RevvyStatusCode.INTEGRITY_ERROR)

    # List test scenarios here
    failed = 0
    total = 0
    try:
        for scenario in scenarios:
            success = False
            try:
                total += 1
                log(f"Running scenario: {scenario.__name__}")
                success = run_scenario(scenario, interface)
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

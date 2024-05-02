#!/usr/bin/python3

""" Main entry point for the revvy service. """

import sys
import traceback
from revvy.firmware_updater import update_firmware_if_needed

from revvy.hardware_dependent.rrrc_transport_i2c import RevvyTransportI2C
from revvy.robot_manager import RobotManager, RevvyStatusCode
from revvy.bluetooth.ble_revvy import RevvyBLE

from revvy.utils.logger import get_logger
from revvy.utils.directories import CURRENT_INSTALLATION_PATH

from tools.check_manifest import check_manifest

# Load the error reporter and init the singleton that'll catch system errors.
from revvy.utils.error_reporter import revvy_error_handler

log = get_logger("revvy.py")

if __name__ == "__main__":
    # Is the script started with --debug?
    is_debug = "--debug" in sys.argv
    if not is_debug:
        revvy_error_handler.register_uncaught_exception_handler()

    log(f"pack: {CURRENT_INSTALLATION_PATH}")
    log(f"file: {__file__}")

    # Check SW version package. If the manifest file is broken, do not launch!
    if not check_manifest("manifest.json"):
        log("Revvy not started because manifest is invalid")
        sys.exit(RevvyStatusCode.INTEGRITY_ERROR)

    interface = RevvyTransportI2C(bus=1)

    ### Before we enter the main loop, let's load up
    if not update_firmware_if_needed(interface):
        log("Revvy not started because the robot has no functional firmware")
        # exiting with integrity error forces the loader to try a previous package
        sys.exit(RevvyStatusCode.INTEGRITY_ERROR)

    # Handles robot state
    robot_manager = RobotManager(interface)

    # Receives commands from the control interface, acts on the robot_manager.
    bluetooth_controller = RevvyBLE(robot_manager)

    if is_debug:
        from revvy.api.websocket import RobotWebSocketApi

        RobotWebSocketApi(robot_manager)

    try:
        # Give visual indication to the user that something is happening
        robot_manager.robot_start()

        # Start up the wireless controller interface
        bluetooth_controller.start()

        # Play a sound to indicate that the robot is ready
        robot_manager._robot.play_tune("s_bootup")

        log("Press Enter to exit")
        input()
        # manual exit
        ret_val = RevvyStatusCode.OK
    except EOFError:
        robot_manager.needs_interrupting = False
        ret_val = robot_manager.wait_for_exit()
    except KeyboardInterrupt:
        # manual exit or update request
        ret_val = robot_manager.status_code
    except Exception:
        log(traceback.format_exc())
        ret_val = RevvyStatusCode.ERROR
    finally:
        log("stopping")
        robot_manager.robot_stop()

    log("terminated")
    sys.exit(ret_val)

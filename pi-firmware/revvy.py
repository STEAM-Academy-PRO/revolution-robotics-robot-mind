#!/usr/bin/python3
# pylint: disable=missing-module-docstring

""" Main entry point for the revvy service. """


import argparse
import sys
import traceback
from revvy.firmware_updater import update_firmware_if_needed

from revvy.robot_manager import RobotManager, RevvyStatusCode
from revvy.bluetooth.ble_revvy import RevvyBLE

from revvy.utils.logger import get_logger
from revvy.utils.directories import CURRENT_INSTALLATION_PATH

from tools.check_manifest import check_manifest

# Load the error reporter and init the singleton that'll catch system errors.
# noinspection unused-import
from revvy.utils.error_reporter import revvy_error_handler

log = get_logger('revvy.py')

parser = argparse.ArgumentParser(description='Revvy PI firmware')
parser.add_argument('--debug', action='store_true', help='Enable debug mode')
args = parser.parse_args()

if not args.debug:
    revvy_error_handler.register_uncaught_exception_handler()

if __name__ == "__main__":
    log(f'pack: {CURRENT_INSTALLATION_PATH}')
    log(f'file: {__file__}')

    # Check SW version package. If the manifest file is broken, do not launch!
    if not check_manifest('manifest.json'):
        log('Revvy not started because manifest is invalid')
        sys.exit(RevvyStatusCode.INTEGRITY_ERROR)

    ### Before we enter the main loop, let's load up
    if not update_firmware_if_needed():
        log('Revvy not started because the robot has no functional firmware')
        # exiting with integrity error forces the loader to try a previous package
        sys.exit(RevvyStatusCode.INTEGRITY_ERROR)

    # Handles robot state
    robot_manager = RobotManager()

    # Receives commands from the control interface, acts on the robot_manager.
    bluetooth_controller = RevvyBLE(robot_manager)

    if args.debug:
        from revvy.api.websocket import RobotWebSocketApi
        RobotWebSocketApi(robot_manager)

    # noinspection PyBroadException
    try:
        bluetooth_controller.start()

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
        log('stopping')
        robot_manager.robot_stop()

    log('terminated')
    sys.exit(ret_val)

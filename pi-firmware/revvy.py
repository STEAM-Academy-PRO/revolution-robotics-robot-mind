#!/usr/bin/python3
# pylint: disable=missing-module-docstring

""" Main entry point for the revvy service. """


import os
import sys
import traceback
# from revvy.api.v1 import RobotWebApi

from revvy.robot_manager import RobotManager, RevvyStatusCode
from revvy.utils.observable import Observable
from revvy.bluetooth.ble_revvy import RevvyBLE
from revvy.utils.error_handler import register_uncaught_exception_handler
from revvy.utils.file_storage import FileStorage, create_unique_file
from revvy.utils.functions import get_serial, read_json
from revvy.utils.version import Version
from revvy.utils.logger import get_logger, logger, LogLevel

from tools.check_manifest import check_manifest

log = get_logger('revvy.py')

if __name__ == "__main__":
    current_installation = os.path.dirname(os.path.realpath(__file__))
    os.chdir(current_installation)
    log(f'pack: {current_installation}')
    log(f'file: {__file__}')

    # base directories
    writeable_data_dir = os.path.join('..', '..', '..', 'user')

    data_dir = os.path.join(writeable_data_dir, 'data')

    # self-test
    if not check_manifest('manifest.json'):
        log('Revvy not started because manifest is invalid')
        sys.exit(RevvyStatusCode.INTEGRITY_ERROR)

    register_uncaught_exception_handler()

    # prepare environment

    serial = get_serial()

    manifest = read_json('manifest.json')
    sw_version = Version(manifest['version'])

    if manifest['branch'] in ['HEAD', 'master']:
        logger.minimum_level = LogLevel.INFO
    else:
        logger.minimum_level = LogLevel.DEBUG

    def on_log_flush(buffer):
        """ Dump flashed framework version"""
        with create_unique_file(os.path.join(data_dir, 'revvy_log')) as file:
            file.write(f"Framework version: {sw_version}-{manifest['branch']}\n")
            file.writelines(buffer)

    logger.on_flush = on_log_flush

    device_storage = FileStorage(data_dir)


    # noinspection PyBroadException
    try:
        device_name = device_storage.read('device-name').decode("ascii")

        if 0 == len(device_name) or len(device_name) > 15:
            device_name = f'Revvy_{serial}'
    except Exception:
        device_name = f'Revvy_{serial}'

    log(f'Device name: {device_name}')

    device_name = Observable(device_name)
    device_name.subscribe(lambda v: device_storage.write('device-name', v.encode("utf-8")))

    writeable_assets_dir = os.path.join(writeable_data_dir, 'assets')

    # Handles robot state
    robot_manager = RobotManager(sw_version, writeable_assets_dir)

    # Receives commands from the control interface, acts on the robot_manager.
    bluetooth_controller = RevvyBLE(robot_manager, device_name,
                                    serial, writeable_data_dir, writeable_assets_dir)

    # RobotWebApi(robot_manager).run()

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

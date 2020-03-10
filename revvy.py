#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-only
import io
import os
import shutil
import sys
import tarfile
import traceback
from contextlib import suppress
from functools import partial

from revvy.revvy_utils import RobotBLEController, RevvyStatusCode
from revvy.robot.robot import Robot
from revvy.robot.led_ring import RingLed
from revvy.robot.status import RobotStatus
from revvy.scripting.runtime import ScriptDescriptor
from revvy.bluetooth.ble_revvy import Observable, RevvyBLE
from revvy.utils.error_handler import register_uncaught_exception_handler
from revvy.utils.file_storage import FileStorage, MemoryStorage, StorageError, create_unique_file
from revvy.firmware_updater import update_firmware
from revvy.utils.functions import get_serial, read_json, str_to_func
from revvy.bluetooth.longmessage import LongMessageHandler, LongMessageStorage, LongMessageType, LongMessageStatus, \
    ReceivedLongMessage
from revvy.robot_config import empty_robot_config, RobotConfig, ConfigError
from revvy.utils.logger import get_logger
from revvy.utils.progress_indicator import ProgressIndicator
from revvy.utils.version import Version
from revvy.utils.logger import logger, LogLevel

from tools.check_manifest import check_manifest


def extract_asset_longmessage(storage, asset_dir):
    """
    Extract the ASSET_DATA long message into a folder.

    After successfully extracting, store the checksum of the asset message in the .hash file.
    Skip extracting if the long message has the same checksum as stored in the folder.
    The folder will be deleted if exists before decompression.

    :param storage: the source where the asset data message is stored
    :param asset_dir: the destination directory
    """

    asset_status = storage.read_status(LongMessageType.ASSET_DATA)

    if asset_status.status == LongMessageStatus.READY:
        with suppress(Exception):
            with open(os.path.join(asset_dir, '.hash'), 'r') as asset_hash_file:
                stored_hash = asset_hash_file.read()

            if stored_hash == asset_status.md5:
                return

        if os.path.isdir(asset_dir):
            shutil.rmtree(asset_dir)

        message_data = storage.get_long_message(LongMessageType.ASSET_DATA)
        with tarfile.open(fileobj=io.StringIO(message_data), mode="r|gz") as tar:
            tar.extractall(path=asset_dir)

        with open(os.path.join(asset_dir, '.hash'), 'w') as asset_hash_file:
            asset_hash_file.write(asset_status.md5)


class LongMessageImplementation:
    # TODO: this, together with the other long message classes is probably a lasagna worth simplifying
    def __init__(self, robot_manager: RobotBLEController, asset_dir, ignore_config):
        self._robot = robot_manager
        self._ignore_config = ignore_config
        self._asset_dir = asset_dir
        self._progress = None

        self._log = get_logger("LongMessageImplementation")

    def on_upload_started(self, message: ReceivedLongMessage):
        """Visual indication that an upload has started

        Requests LED ring change in the background"""

        message_type = message.message_type
        if message_type == LongMessageType.FRAMEWORK_DATA:
            self._progress = ProgressIndicator(self._robot.robot.led, message.total_chunks, 0x00FF00, 0xFF00FF)
        else:
            self._progress = None
            self._robot.robot.status.robot_status = RobotStatus.Configuring

    def on_upload_progress(self, message: ReceivedLongMessage):
        """Indicate long message download progress"""
        if self._progress:
            if message.total_chunks == 0:
                # calculate approximate chunk count
                expected_size = 250000
                chunk_size = len(message.data) / message.received_chunks
                message.total_chunks = expected_size / chunk_size
                self._progress.end = message.total_chunks

            if message.total_chunks != 0:
                self._log(f'Progress: {message.received_chunks}/{message.total_chunks}')
                self._progress.update(message.received_chunks)

    def on_transmission_finished(self, message: ReceivedLongMessage):
        """Visual indication that an upload has finished

        Requests LED ring change in the background"""

        message_type = message.message_type
        if message_type == LongMessageType.FRAMEWORK_DATA:
            if not message.is_valid:
                self._log('Firmware update cancelled')
                self._progress = None
                self._robot.run_in_background(partial(self._robot.robot.led.start_animation, RingLed.BreathingGreen))
        else:
            # don't schedule on background, the robot will be restarted before setting the LEDs
            if self._progress:
                self._progress.set_indeterminate()

    def on_message_updated(self, storage, message: ReceivedLongMessage):
        message_type = message.message_type
        self._log(f'Received message: {message_type}')

        if message_type == LongMessageType.TEST_KIT:
            test_script_source = storage.get_long_message(message_type).decode()
            self._log(f'Running test script: {test_script_source}')

            script_descriptor = ScriptDescriptor("test_kit", str_to_func(test_script_source), 0)

            def start_script():
                self._log("Starting new test script")
                handle = self._robot._scripts.add_script(script_descriptor)
                handle.on_stopped(partial(self._robot.configure, None))

                # start can't run in on_stopped handler because overwriting script causes deadlock
                self._robot.run_in_background(handle.start)

            self._robot.configure(empty_robot_config, start_script)

        elif message_type == LongMessageType.CONFIGURATION_DATA:
            message_data = storage.get_long_message(message_type).decode()
            self._log(f'New configuration: {message_data}')

            try:
                parsed_config = RobotConfig.from_string(message_data)

                if self._ignore_config:
                    self._log('New configuration ignored')
                else:
                    self._robot.configure(parsed_config, self._robot.start_remote_controller)
            except ConfigError:
                self._log(traceback.format_exc())

        elif message_type == LongMessageType.FRAMEWORK_DATA:
            self._robot.robot.status.robot_status = RobotStatus.Updating
            self._progress.set_indeterminate()
            self._robot.request_update()

        elif message_type == LongMessageType.ASSET_DATA:
            extract_asset_longmessage(storage, self._asset_dir)


if __name__ == "__main__":
    current_installation = os.path.dirname(os.path.realpath(__file__))
    os.chdir(current_installation)
    print(f'Revvy run from {current_installation} ({__file__})')

    # base directories
    writeable_data_dir = os.path.join('..', '..', '..', 'user')

    ble_storage_dir = os.path.join(writeable_data_dir, 'ble')
    data_dir = os.path.join(writeable_data_dir, 'data')

    # self-test
    if not check_manifest('manifest.json'):
        print('Revvy not started because manifest is invalid')
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
        with create_unique_file(os.path.join(data_dir, 'revvy_log')) as file:
            file.write(f"Framework version: {sw_version}-{manifest['branch']}")
            file.writelines(buffer)

    logger.on_flush = on_log_flush

    device_storage = FileStorage(data_dir)
    ble_storage = FileStorage(ble_storage_dir)

    writeable_assets_dir = os.path.join(writeable_data_dir, 'assets')

    try:
        device_name = device_storage.read('device-name').decode("utf-8")
    except StorageError:
        device_name = f'Revvy_{serial}'

    print(f'Device name: {device_name}')

    device_name = Observable(device_name)
    device_name.subscribe(lambda v: device_storage.write('device-name', v.encode("utf-8")))

    long_message_storage = LongMessageStorage(ble_storage, MemoryStorage())
    extract_asset_longmessage(long_message_storage, writeable_assets_dir)

    with Robot() as robot:
        robot.assets.add_source(writeable_assets_dir)

        try:
            update_firmware(os.path.join('data', 'firmware'), robot)
        except TimeoutError:
            print('Failed to update firmware')

        long_message_handler = LongMessageHandler(long_message_storage)
        robot_manager = RobotBLEController(robot, sw_version, RevvyBLE(device_name, serial, long_message_handler))

        lmi = LongMessageImplementation(robot_manager, writeable_assets_dir, False)
        long_message_handler.on_upload_started(lmi.on_upload_started)
        long_message_handler.on_upload_progress(lmi.on_upload_progress)
        long_message_handler.on_upload_finished(lmi.on_transmission_finished)
        long_message_handler.on_message_updated(lmi.on_message_updated)

        # noinspection PyBroadException
        try:
            robot_manager.start()

            print("Press Enter to exit")
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
            print(traceback.format_exc())
            ret_val = RevvyStatusCode.ERROR
        finally:
            print('stopping')
            robot_manager.stop()

    print('terminated.')
    sys.exit(ret_val)

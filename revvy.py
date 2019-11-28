#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-only
import io
import shutil
import tarfile

from revvy.utils.assets import Assets
from revvy.bluetooth.ble_revvy import Observable, RevvyBLE
from revvy.utils.file_storage import FileStorage, MemoryStorage, StorageError
from revvy.firmware_updater import McuUpdater, McuUpdateManager
from revvy.utils.functions import get_serial, read_json
from revvy.bluetooth.longmessage import LongMessageHandler, LongMessageStorage, LongMessageType, LongMessageStatus
from revvy.hardware_dependent.rrrc_transport_i2c import RevvyTransportI2C
from revvy.robot_config import empty_robot_config
from revvy.revvy_utils import *
from revvy.mcu.rrrc_transport import *
from revvy.mcu.rrrc_control import *
import sys

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
        # noinspection PyBroadException
        try:
            with open(os.path.join(asset_dir, '.hash'), 'r') as asset_hash_file:
                stored_hash = asset_hash_file.read()

            if stored_hash == asset_status.md5:
                return
        except Exception:
            pass

        if os.path.isdir(asset_dir):
            shutil.rmtree(asset_dir)

        message_data = storage.get_long_message(LongMessageType.ASSET_DATA)
        with tarfile.open(fileobj=io.StringIO(message_data), mode="r|gz") as tar:
            tar.extractall(path=asset_dir)

        with open(os.path.join(asset_dir, '.hash'), 'w') as asset_hash_file:
            asset_hash_file.write(asset_status.md5)


class LongMessageImplementation:
    # TODO: this, together with the other long message classes is probably a lasagna worth simplifying
    def __init__(self, robot_manager: RobotManager, ignore_config):
        self._robot = robot_manager
        self._ignore_config = ignore_config

    def on_upload_started(self, message_type):
        """Visual indication that an upload has started

        Requests LED ring change in the background"""

        if message_type == LongMessageType.FRAMEWORK_DATA:
            self._robot.run_in_background(lambda: self._robot.robot.led_ring.set_scenario(RingLed.ColorWheel))
        else:
            self._robot.robot.status.robot_status = RobotStatus.Configuring

    def on_transmission_finished(self, message_type):
        """Visual indication that an upload has finished

        Requests LED ring change in the background"""

        if message_type != LongMessageType.FRAMEWORK_DATA:
            self._robot.run_in_background(lambda: self._robot.robot.led_ring.set_scenario(RingLed.BreathingGreen))

    def on_message_updated(self, storage, message_type):
        print('Received message: {}'.format(message_type))

        if message_type == LongMessageType.TEST_KIT:
            message_data = storage.get_long_message(message_type).decode()
            print('Running test script: {}'.format(message_data))

            robot_manager = self._robot

            def start_script():
                print("Starting new test script")
                robot_manager._scripts.add_script("test_kit", message_data, 0)
                robot_manager._scripts["test_kit"].on_stopped(lambda: robot_manager.configure(None))

                # start can't run in on_stopped handler because overwriting script causes deadlock
                robot_manager.run_in_background(lambda: robot_manager._scripts["test_kit"].start())

            self._robot.configure(empty_robot_config, start_script)

        elif message_type == LongMessageType.CONFIGURATION_DATA:
            message_data = storage.get_long_message(message_type).decode()
            print('New configuration: {}'.format(message_data))
            if self._ignore_config:
                print('New configuration ignored')
            else:
                parsed_config = RobotConfig.from_string(message_data)
                if parsed_config is not None:
                    self._robot.configure(parsed_config, self._robot.start_remote_controller)

        elif message_type == LongMessageType.FRAMEWORK_DATA:
            self._robot.robot.status.robot_status = RobotStatus.Updating
            self._robot.request_update()

        elif message_type == LongMessageType.ASSET_DATA:
            asset_dir = os.path.join('..', '..', '..', 'user', 'assets')
            extract_asset_longmessage(storage, asset_dir)


if __name__ == "__main__":
    current_installation = os.path.dirname(os.path.realpath(__file__))
    os.chdir(current_installation)

    # base directories
    writeable_data_dir = os.path.join(current_installation, '..', '..', '..', 'user')
    package_data_dir = os.path.join(current_installation, 'data')

    ble_storage_dir = os.path.join(writeable_data_dir, 'ble')
    data_dir = os.path.join(writeable_data_dir, 'data')

    # self-test
    if not check_manifest(os.path.join(current_installation, 'manifest.json')):
        print('Revvy not started because manifest is invalid')
        sys.exit(RevvyStatusCode.INTEGRITY_ERROR)

    def log_uncaught_exception(exctype, value, tb):
        log_message = 'Uncaught exception: {}\n' \
                      'Value: {}\n' \
                      'Traceback: \n\t{}\n' \
                      '\n'.format(exctype, value, "\t".join(traceback.format_tb(tb)))
        print(log_message)
        logfile = os.path.join(data_dir, 'revvy_crash.log')

        with open(logfile, 'a') as logf:
            logf.write(log_message)

    sys.excepthook = log_uncaught_exception

    print('Revvy run from {} ({})'.format(current_installation, __file__))

    # prepare environment

    serial = get_serial()

    manifest = read_json('manifest.json')

    device_storage = FileStorage(data_dir)
    ble_storage = FileStorage(ble_storage_dir)

    assets = Assets([
        os.path.join(package_data_dir, 'assets'),
        os.path.join(writeable_data_dir, 'assets')
    ])

    try:
        device_name = device_storage.read('device-name').decode("utf-8")
    except StorageError:
        device_name = 'Revvy_{}'.format(serial)

    print('Device name: {}'.format(device_name))

    device_name = Observable(device_name)
    device_name.subscribe(lambda v: device_storage.write('device-name', v.encode("utf-8")))

    long_message_storage = LongMessageStorage(ble_storage, MemoryStorage())
    extract_asset_longmessage(long_message_storage, os.path.join(writeable_data_dir, 'assets'))

    with RevvyTransportI2C() as transport:
        robot_control = RevvyControl(transport.bind(0x2D))
        bootloader_control = BootloaderControl(transport.bind(0x2B))

        updater = McuUpdater(robot_control, bootloader_control)
        update_manager = McuUpdateManager(os.path.join(package_data_dir, 'firmware'), updater)
        update_manager.update_if_necessary()

        long_message_handler = LongMessageHandler(long_message_storage)
        ble = RevvyBLE(device_name, serial, long_message_handler)
        robot = RobotManager(
            robot_control,
            ble,
            lambda sound: assets.get_asset_file('sounds', sound),
            manifest['version'])

        lmi = LongMessageImplementation(robot, False)
        long_message_handler.on_upload_started(lmi.on_upload_started)
        long_message_handler.on_upload_finished(lmi.on_transmission_finished)
        long_message_handler.on_message_updated(lmi.on_message_updated)

        # noinspection PyBroadException
        try:
            robot.start()

            print("Press Enter to exit")
            input()
            # manual exit
            ret_val = RevvyStatusCode.OK
        except EOFError:
            robot.needs_interrupting = False
            while not robot.exited:
                time.sleep(1)
            ret_val = robot.status_code
        except KeyboardInterrupt:
            # manual exit or update request
            ret_val = robot.status_code
        except Exception:
            print(traceback.format_exc())
            ret_val = RevvyStatusCode.ERROR
        finally:
            print('stopping')
            robot.stop()

        print('terminated.')
    sys.exit(ret_val)

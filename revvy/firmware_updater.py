# SPDX-License-Identifier: GPL-3.0-only

import binascii
import os
import time
import traceback
from json import JSONDecodeError

from revvy.utils.file_storage import IntegrityError
from revvy.utils.logger import get_logger
from revvy.utils.version import Version
from revvy.utils.functions import split, bytestr_hash, read_json
from revvy.mcu.rrrc_control import BootloaderControl, RevvyControl

op_mode_application = 0xAA
op_mode_bootloader = 0xBB


class McuUpdater:
    def __init__(self, robot_control: RevvyControl, bootloader_control: BootloaderControl):
        self._robot = robot_control
        self._bootloader = bootloader_control

        self._log = get_logger('McuUpdater')

    def _read_operation_mode(self):
        start_time = time.time()
        while (time.time() - start_time) < 10:
            try:
                return self._robot.read_operation_mode()
            except OSError:
                try:
                    return self._bootloader.read_operation_mode()
                except OSError:
                    self._log("Failed to read operation mode. Retrying")
                    time.sleep(0.5)

        raise TimeoutError('Could not determine operation mode')

    def _finalize_update(self):
        """
        Finalize firmware and reboot to application
        """
        # noinspection PyBroadException
        try:
            self._bootloader.finalize_update()
            # at this point, the bootloader shall start the application
        except OSError:
            self._log('MCU restarted before finishing communication')
        except Exception:
            traceback.print_exc()

    def _request_bootloader_mode(self):
        try:
            self._log("Rebooting to bootloader")
            self._robot.reboot_bootloader()
        except OSError:
            self._log('MCU restarted before finishing communication')

    def read_hardware_version(self):
        """
        Read the hardware version from the MCU
        """
        mode = self._read_operation_mode()
        if mode == op_mode_application:
            return self._robot.get_hardware_version()
        else:
            return self._bootloader.get_hardware_version()

    def is_update_needed(self, fw_version: Version):
        """
        Compare firmware version to the currently running one
        """
        mode = self._read_operation_mode()
        if mode == op_mode_application:
            fw = self._robot.get_firmware_version()
            return fw != fw_version  # allow downgrade as well
        else:
            # in bootloader mode, probably no firmware, request update
            return True

    def reboot_to_bootloader(self):
        """
        Start the bootloader on the MCU

        This function checks the operating mode. Reboot is only requested when in application mode
        """
        mode = self._read_operation_mode()
        if mode == op_mode_application:
            self._request_bootloader_mode()
            # wait for the reboot to complete
            mode = self._read_operation_mode()
            assert mode == op_mode_bootloader

    def update_firmware(self, new_version: Version, data):
        """
        Compare firmware version and burn it in case the version differs
        """

        if self.is_update_needed(new_version):
            self.reboot_to_bootloader()

            checksum = binascii.crc32(data)
            self._log("Image info: size: {} checksum: {}".format(len(data), checksum))

            # init update
            self._log("Initializing update")
            self._bootloader.send_init_update(len(data), checksum)

            # split data into chunks
            chunks = split(data, chunk_size=255)

            # send data
            self._log('Sending data')
            start = time.time()
            for chunk in chunks:
                self._bootloader.send_firmware(chunk)
            self._log('Data transfer took {} seconds'.format(round(time.time() - start, 1)))

            self._finalize_update()

            # read operating mode - this should return only when application has started
            assert self._read_operation_mode() == op_mode_application


class McuUpdateManager:
    def __init__(self, fw_dir, updater):
        self._fw_dir = fw_dir
        self._updater = updater

        self._log = get_logger('McuUpdateManager')

    def _read_catalog(self):
        try:
            fw_metadata = read_json(os.path.join(self._fw_dir, 'catalog.json'))

            # hw version -> fw version mapping
            return {Version(version): {
                'version': Version(fw_metadata[version]['version']),
                'file': os.path.join(self._fw_dir, fw_metadata[version]['filename']),
                'md5': fw_metadata[version]['md5'],
                'length': fw_metadata[version]['length'],
            } for version in fw_metadata}

        except (IOError, JSONDecodeError, KeyError):
            return {}

    def _read_firmware(self, fw_data):
        with open(fw_data['file'], "rb") as f:
            firmware_binary = f.read()

        if len(firmware_binary) != fw_data['length']:
            self._log('Firmware file length check failed, aborting')
            raise IntegrityError("Firmware file length does not match")

        checksum = bytestr_hash(firmware_binary)
        if checksum != fw_data['md5']:
            self._log('Firmware file integrity check failed, aborting')
            raise IntegrityError("Firmware file checksum does not match")

        return firmware_binary

    def update_if_necessary(self):
        hw_version = self._updater.read_hardware_version()

        firmware_collection = self._read_catalog()

        try:
            fw_data = firmware_collection[hw_version]
            firmware_binary = self._read_firmware(fw_data)
            self._updater.update_firmware(fw_data['version'], firmware_binary)

        except KeyError:
            self._log(traceback.format_exc())
            self._log('No firmware for the hardware ({})'.format(hw_version))

        except IOError:
            self._log(traceback.format_exc())
            self._log('Firmware file does not exist or is not readable')

        except IntegrityError:
            self._log(traceback.format_exc())
            self._log('Firmware file corrupted')

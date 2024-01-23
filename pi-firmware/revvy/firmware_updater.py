
import binascii
import os
import time
import traceback
from contextlib import suppress
from json import JSONDecodeError
from revvy.hardware_dependent.rrrc_transport_i2c import RevvyTransportI2C

from revvy.utils.file_storage import IntegrityError
from revvy.utils.logger import get_logger
from revvy.utils.stopwatch import Stopwatch
from revvy.utils.version import Version
from revvy.utils.functions import split, bytestr_hash, read_json
from revvy.mcu.rrrc_control import RevvyTransportBase

log = get_logger('McuUpdater')

class McuUpdater:
    """ Manages version updates """
    def __init__(self, revvy_transport_base: RevvyTransportBase):
        self._application_controller = revvy_transport_base.create_application_control()
        self._bootloader_controller = revvy_transport_base.create_bootloader_control()
        self._stopwatch = Stopwatch()
        self.is_bootloader_mode = self._is_in_bootloader_mode()
        self.hw_version = self.read_hw_version()

    def _is_in_bootloader_mode(self) -> bool:
        """
            Tries to connect to the board and determine,
            if it's in bootloader mode or application mode
        """
        self._stopwatch.reset()
        while self._stopwatch.elapsed < 10:
            with suppress(OSError):
                self._application_controller.read_operation_mode()
                return False

            with suppress(OSError):
                self._bootloader_controller.read_operation_mode()
                return True

            # log("Failed to read operation mode. Retrying")
            time.sleep(0.5)

        raise TimeoutError('Could not connect to Board! Bailing.')


    def read_hw_version(self):
        """ Reads the board's version through the i2c interface """
        if self.is_bootloader_mode:
            return self._bootloader_controller.get_hardware_version()
        else:
            return self._application_controller.get_hardware_version()


    def is_update_needed(self, bin_file_fw_version: Version, fw_crc):
        """
        Compare firmware version to the currently running one
        """

        if not self.is_bootloader_mode:
            fw = self._application_controller.get_firmware_version()
            if fw != bin_file_fw_version:  # allow downgrade as well
                log(f'Firmware version is not latest, updating. {fw}')
                return True

            self.reboot_to_bootloader()

            log('Checking CRC...')

            crc = self._bootloader_controller.read_firmware_crc()

            is_crc_different = crc != fw_crc
            if is_crc_different:
                log(f'Firmware CRC check failed! {crc} != {fw_crc}')
            else:
                log('Firmware CRC matches, skipping update.')
            return is_crc_different
        else:
            # in bootloader mode, probably no firmware, request update
            return True


    def reboot_to_bootloader(self):
        """
        Start the bootloader on the MCU

        This function checks the operating mode. Reboot is only requested when in application mode
        """
        if not self.is_bootloader_mode:
            try:
                log("Rebooting to bootloader (Pink LEDs)")
                self._application_controller.reboot_bootloader()
            except OSError:
                # In this place, we expect an error because the application
                # reboots before responding.
                pass

            time.sleep(0.2)

            self.is_bootloader_mode = self._is_in_bootloader_mode()

        assert self.is_bootloader_mode


    def upload_binary(self, checksum, data):
        """ Send the firmware to the MCU through the transport layer. """
        self.reboot_to_bootloader()

        log(f"Image info: size: {len(data)} checksum: {checksum}")

        # init update
        log("Initializing update")
        self._bootloader_controller.send_init_update(len(data), checksum)

        # split data into chunks
        chunks = split(data, chunk_size=255)

        # send data
        log('Sending data')
        self._stopwatch.reset()
        for chunk in chunks:
            self._bootloader_controller.send_firmware(chunk)
        log(f'Data transfer took {round(self._stopwatch.elapsed, 1)} seconds')


    def finalize_and_start_application(self, was_update_needed):
        """
            Call finalize firmware on the board then reboot to application
        """
        try:
            self._bootloader_controller.finalize_update()
        except OSError:
            # In this place, we expect an error because the bootloader reboots before responding.
            pass
        except Exception:
            log(traceback.format_exc())

        time.sleep(0.2)
        assert not self._is_in_bootloader_mode()

        fw = self._application_controller.get_firmware_version()

        if was_update_needed:
            log(f'Update successful, running FW version {fw}')
        else:
            log(f'No update was needed, running FW version {fw}')



def read_firmware_bin_from_fs(fw_data):
    """ Finds the bin file from the package and reads them out, and checks MD5 """
    with open(fw_data['file'], "rb") as f:
        firmware_binary = f.read()

    if len(firmware_binary) != fw_data['length']:
        log('Firmware file length check failed, aborting')
        raise IntegrityError("Firmware file length does not match")

    checksum = bytestr_hash(firmware_binary)
    if checksum != fw_data['md5']:
        log('Firmware file integrity check failed, aborting')
        raise IntegrityError("Firmware file checksum does not match")

    return firmware_binary


def get_firmware_for_hw_version(fw_dir, hw_version):
    """ MCU firmware version existing in the current package """
    try:
        fw_metadata = read_json(os.path.join(fw_dir, 'catalog.json'))
        version = str(hw_version)

        data = {
            'file': os.path.join(fw_dir, fw_metadata[version]['filename']),
            'md5': fw_metadata[version]['md5'],
            'length': fw_metadata[version]['length'],
        }
        return Version(fw_metadata[version]['version']), read_firmware_bin_from_fs(data)

    except (IOError, JSONDecodeError, KeyError) as e:
        log(traceback.format_exc())
        raise KeyError from e


def update_firmware_if_needed():
    """ Checks HW version, determines if we need a """
    firmware_path = os.path.join('data', 'firmware')

    ### If we are in bootloader mode, we DO have to update.
    ### If we are in application mode, we have to update only if the version is not the same.

    ### Determine if we are in application mode.

    i2c_bus = 1
    updater = McuUpdater(RevvyTransportI2C(i2c_bus))

    try:
        fw_bin_version, fw_binary = get_firmware_for_hw_version(firmware_path, updater.hw_version)
    except KeyError as e:
        log(f'No firmware for the hardware ({updater.hw_version})')
        if updater.is_bootloader_mode:
            raise e
    except IOError as e:
        log('Firmware file does not exist or is not readable')
        if updater.is_bootloader_mode:
            raise e
    except IntegrityError as e:
        log('Firmware file corrupted')
        if updater.is_bootloader_mode:
            raise e

    checksum = binascii.crc32(fw_binary)

    is_update_needed = updater.is_update_needed(fw_bin_version, checksum)
    if is_update_needed:
        updater.upload_binary(checksum, fw_binary)

    # Very important: this is ALWAYS needed to reset back the MCU state to application mode.
    updater.finalize_and_start_application(is_update_needed)

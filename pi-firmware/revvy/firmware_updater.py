"""
    Manages update system of the MCU board.

    First, check if the board is in bootloader mode or application mode.

    - If it's in application mode, we have a working firmware currently running.
        - reboot to bootloader mode, check if the CRC of the flashed image is equal
          to the latest in our file system.
           - if not, update is needed.
    - If bootloader mode, we do not have a running firmware -> something is wrong
      let's try to flash the MCU.
    - Reads hardware version out from the bootloader state
    - Checks if we have a bin for the hardware version.
    - if yes, and update is needed, we try uploading the image.
    - when done, always restart the MCU, making it boot to application mode
    - if the happy path works, we are in the app, we can continue loading.
    - on the sad path, we raise an exception that fails the app, and the loader tries over.
"""

import binascii
import os
import time
import traceback
from contextlib import suppress
from json import JSONDecodeError
from typing import Optional

from revvy.utils.file_storage import IntegrityError
from revvy.utils.logger import get_logger
from revvy.utils.stopwatch import Stopwatch
from revvy.utils.version import VERSION, Version, get_sw_version
from revvy.utils.functions import split, bytestr_hash, read_json
from revvy.mcu.rrrc_control import RevvyTransportBase
from revvy.mcu.commands import UnknownCommandError

log = get_logger("McuUpdater")


class McuUpdater:
    """Manages version updates"""

    def __init__(self, revvy_transport_base: RevvyTransportBase):
        self._application_controller = revvy_transport_base.create_application_control()
        self._bootloader_controller = revvy_transport_base.create_bootloader_control()
        self._stopwatch = Stopwatch()
        self.is_bootloader_mode = self._is_in_bootloader_mode()

        hw_version = self.read_hw_version()
        assert hw_version is not None, "Could not read hardware version, unable to proceed"
        self.hw_version: Version = hw_version

        # Will populate it in finalize.
        self.fw_version = None
        self.sw_version = get_sw_version()

        self.update_global_version_info()

    def _is_in_bootloader_mode(self) -> bool:
        """
        Tries to connect to the board and determine,
        if it's in bootloader mode or application mode.

        This function uses arbitrary MCU commands that have no side effects. Connection is
        determined by the success of the command.
        """
        self._stopwatch.reset()
        while self._stopwatch.elapsed < 10:
            with suppress(OSError):
                self._application_controller.ping()
                return False

            with suppress(OSError):
                self._bootloader_controller.get_hardware_version()
                return True

            # log("Failed to read operation mode. Retrying")
            time.sleep(0.5)

        raise TimeoutError("Could not connect to Board! Bailing.")

    def read_hw_version(self) -> Optional[Version]:
        """Reads the board's version through the i2c interface"""
        if self.is_bootloader_mode:
            return self._bootloader_controller.get_hardware_version()
        else:
            return self._application_controller.get_hardware_version()

    def is_update_needed(self, bin_file_fw_version: Version, fw_crc: int):
        """
        Compare firmware version to the currently running one
        """

        if self.is_bootloader_mode:
            # in bootloader mode, probably no firmware, request update
            return True

        fw = self._application_controller.get_firmware_version()
        if fw != bin_file_fw_version:  # allow downgrade as well
            log(f"Firmware version is not latest, updating. {fw}")
            return True

        log("Checking CRC...")

        try:
            crc = self._application_controller.read_firmware_crc()
        except UnknownCommandError:
            log(f"Updating old firmware that does not support reading CRC")
            return True

        is_crc_different = crc != fw_crc
        if is_crc_different:
            log(f"Firmware CRC check failed! {crc} != {fw_crc}")
        else:
            log("Firmware CRC matches, skipping update.")

        return is_crc_different

    def reboot_to_bootloader(self) -> None:
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

    def upload_binary(self, checksum: int, data: bytes):
        """Send the firmware to the MCU through the transport layer."""
        self.reboot_to_bootloader()

        log(f"Image info: size: {len(data)} checksum: {checksum}")

        # init update
        log("Initializing update")
        self._bootloader_controller.send_init_update(len(data), checksum)

        # split data into chunks
        chunks = split(data, chunk_size=255)

        # send data
        log("Sending data")
        self._stopwatch.reset()
        for chunk in chunks:
            self._bootloader_controller.send_firmware(chunk)
        log(f"Data transfer took {round(self._stopwatch.elapsed, 1)} seconds")

    def finalize_and_start_application(self, was_update_needed: bool):
        """
        Call finalize firmware on the board then reboot to application
        """
        try:
            self._bootloader_controller.finalize_update()
        except OSError:
            # In this place, we ignore errors because the bootloader may reboot.
            pass
        except Exception:
            log(traceback.format_exc())

        time.sleep(0.2)
        assert not self._is_in_bootloader_mode()

        self.fw_version = self._application_controller.get_firmware_version()
        self.update_global_version_info()

        if was_update_needed:
            log(f"Update successful, running FW version {self.fw_version}")
        else:
            log(f"No update was needed, running FW version {self.fw_version}")

    def update_global_version_info(self) -> None:
        VERSION.set(self.sw_version, self.hw_version, self.fw_version)


def read_firmware_bin_from_fs(fw_data: dict[str, str]) -> bytes:
    """Finds the bin file from the package and reads them out, and checks MD5"""
    with open(fw_data["file"], "rb") as f:
        firmware_binary = f.read()

    if len(firmware_binary) != fw_data["length"]:
        log("Firmware file length check failed, aborting")
        raise IntegrityError("Firmware file length does not match")

    checksum = bytestr_hash(firmware_binary)
    if checksum != fw_data["md5"]:
        log("Firmware file integrity check failed, aborting")
        raise IntegrityError("Firmware file checksum does not match")

    return firmware_binary


def get_firmware_for_hw_version(fw_dir: str, hw_version: Version) -> tuple[Version, bytes]:
    """MCU firmware version existing in the current package"""
    try:
        fw_metadata = read_json(os.path.join(fw_dir, "catalog.json"))
        version = str(hw_version)

        data = {
            "file": os.path.join(fw_dir, fw_metadata[version]["filename"]),
            "md5": fw_metadata[version]["md5"],
            "length": fw_metadata[version]["length"],
        }
        return Version(fw_metadata[version]["version"]), read_firmware_bin_from_fs(data)

    except (IOError, JSONDecodeError, KeyError) as e:
        log(traceback.format_exc())
        raise KeyError from e


def update_firmware_if_needed(interface: RevvyTransportBase) -> bool:
    """
    Checks HW version, determines if we can/need to do a firmware update

    Returns True if the update was skipped or successful, False if the robot is in a
    state where it cannot continue.
    """
    firmware_path = os.path.join("data", "firmware")

    ### If we are in bootloader mode, we DO have to update.
    ### If we are in application mode, we have to update only if the version is not the same.

    ### Determine if we are in application mode.

    updater = McuUpdater(interface)

    # If an exception occurs, we'll save it for later when we may rethrow it.
    exception = None
    fw_bin_version = None
    fw_binary = None

    try:
        fw_bin_version, fw_binary = get_firmware_for_hw_version(firmware_path, updater.hw_version)
    except KeyError as e:
        exception = e
        log(f"No firmware for the hardware ({updater.hw_version})")
    except IOError as e:
        exception = e
        log("Firmware file does not exist or is not readable")
    except IntegrityError as e:
        exception = e
        log("Firmware file corrupted")

    if exception is not None:
        if updater.is_bootloader_mode:
            # We have no valid firmware in the package, and no firmware on the brain. Let's throw an
            # exception, and let the loader try again. Maybe an earier installation will restore
            # the MCU.
            log("No firmware in the package, and no firmware on the brain. Aborting.")
            return False
        else:
            # We have no firmware in the package, but we have one on the brain. Let's continue
            # and hope that the package is compatible.
            log("No firmware in the package. The brain will use the last installation.")
            return True

    # pyright doesn't understand that if we get here, the try: block was successful.
    # It therefore thinks that fw_binary and fw_bin_version can be unbound, unless we
    # set then to None then check here.
    if fw_binary is None or fw_bin_version is None:
        return False

    checksum = binascii.crc32(fw_binary)

    is_update_needed = updater.is_update_needed(fw_bin_version, checksum)
    if is_update_needed:
        updater.upload_binary(checksum, fw_binary)

    # Very important: this is ALWAYS needed to reset back the MCU state to application mode.
    updater.finalize_and_start_application(is_update_needed)
    return True

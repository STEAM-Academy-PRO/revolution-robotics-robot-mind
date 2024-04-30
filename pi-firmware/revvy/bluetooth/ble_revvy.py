""" Bluetooth Low Energy interface for Revvy """

import os
import subprocess
import time
from typing import List
from pybleno import Bleno, BlenoPrimaryService

from revvy.bluetooth.services.battery import CustomBatteryService
from revvy.bluetooth.services.device_information import DeviceInformationService
from revvy.bluetooth.services.long_message import LongMessageService
from revvy.robot.robot_events import RobotEvent
from revvy.scripting.runtime import ScriptEvent

from revvy.utils.device_name import get_device_name
from revvy.utils.directories import BLE_STORAGE_DIR, WRITEABLE_ASSETS_DIR
from revvy.utils.logger import LogLevel, get_logger
from revvy.utils.file_storage import FileStorage, MemoryStorage

from revvy.robot_manager import RobotManager

from revvy.bluetooth.longmessage import LongMessageHandler, LongMessageStorage
from revvy.bluetooth.longmessage import extract_asset_longmessage, LongMessageImplementation

from revvy.bluetooth.live_message_service import LiveMessageService, MotorData

from revvy.utils.error_reporter import revvy_error_handler
from revvy.utils.stopwatch import Stopwatch


class RevvyBLE:
    """
    Revvy Bluetooth Interface

    Listens to connections from the app and controls the robot.
    """

    def __init__(self, robot_manager: RobotManager):
        self._robot_manager = robot_manager

        self._log = get_logger("RevvyBLE")
        os.environ["BLENO_DEVICE_NAME"] = get_device_name()
        self._log(f"Initializing BLE with device name {get_device_name()}")

        ### -----------------------------------------------------
        ### Long Message Handler for receiving files and configs.
        ### -----------------------------------------------------

        ble_storage = FileStorage(BLE_STORAGE_DIR)

        long_message_storage = LongMessageStorage(ble_storage, MemoryStorage())
        extract_asset_longmessage(long_message_storage, WRITEABLE_ASSETS_DIR)
        long_message_handler = LongMessageHandler(long_message_storage)

        lmi = LongMessageImplementation(robot_manager, long_message_storage, WRITEABLE_ASSETS_DIR)
        long_message_handler.on_upload_started.add(lmi.on_upload_started)
        long_message_handler.on_upload_progress.add(lmi.on_upload_progress)
        long_message_handler.on_upload_finished.add(lmi.on_transmission_finished)
        long_message_handler.on_message_updated.add(lmi.on_message_updated)

        ### -----------------------------------------------------
        ### Services
        ### -----------------------------------------------------

        self._dis = DeviceInformationService()
        self._bas = CustomBatteryService()
        self._live = LiveMessageService(robot_manager)
        self._long = LongMessageService(long_message_handler)

        self._named_services = {
            "device_information_service": self._dis,
            "battery_service": self._bas,
            "long_message_service": self._long,
            "live_message_service": self._live,
        }

        self._advertised_uuid_list = [self._live["uuid"]]

        self._bleno = Bleno()

        # _bleno exposes it's on function runtime, which makes the linter sad.
        self._bleno.on(  # pyright: ignore[reportAttributeAccessIssue]
            "stateChange", self._on_state_change
        )
        self._bleno.on(  # pyright: ignore[reportAttributeAccessIssue]
            "advertisingStart", self._on_advertising_start
        )
        self._bleno.on("accept", self._on_connected)  # pyright: ignore[reportAttributeAccessIssue]
        self._bleno.on(  # pyright: ignore[reportAttributeAccessIssue]
            "disconnect", self._on_disconnect
        )

        self.subscribe_to_state_changes()

    def subscribe_to_state_changes(self) -> None:
        """
        Use the event emitter pattern to subscribe to robot status changes
        The robot manager will emit everything we need to communicate back
        to the mobile app.
        """

        self._robot_manager.on(
            RobotEvent.BATTERY_CHANGE,
            lambda ref, val: self._bas.characteristic("unified_battery_status").updateValue(val),
        )

        # Initialize value - this could be prettier, not sure how yet.
        initial_battery_state = self._robot_manager._robot_state._battery.get()
        self._log(f"initial battery state {initial_battery_state}")
        self._bas.characteristic("unified_battery_status").updateValue(initial_battery_state)

        self._robot_manager.on(
            RobotEvent.SENSOR_VALUE_CHANGE,
            lambda ref, sensor_reading: self._live.update_sensor(sensor_reading),
        )

        # Only send up ORIENTATION changes, NO GYRO as we are not using that anywhere.
        self._robot_manager.on(
            RobotEvent.ORIENTATION_CHANGE,
            lambda ref, vector_orientation: self._live.update_orientation(vector_orientation),
        )

        self._robot_manager.on(RobotEvent.DISCONNECT, self.disconnect)

        self._robot_manager.on(
            RobotEvent.SESSION_ID_CHANGE, lambda ref, val: self._live.update_session_id(val)
        )

        self._robot_manager.on(
            RobotEvent.SCRIPT_VARIABLE_CHANGE,
            lambda ref, variables: self._live.update_script_variables(variables),
        )

        self._robot_manager.on(
            RobotEvent.PROGRAM_STATUS_CHANGE,
            lambda ref, script_status_change: self.update_program_status(
                script_status_change.id, script_status_change.status
            ),
        )

        self._robot_manager.on(
            RobotEvent.BACKGROUND_CONTROL_STATE_CHANGE,
            lambda ref, background_script_status_change: self._live.update_state_control(
                background_script_status_change
            ),
        )

        self._robot_manager.on(
            RobotEvent.TIMER_TICK, lambda ref, timer_value: self._live.update_timer(timer_value)
        )

        self._robot_manager.on(RobotEvent.MOTOR_CHANGE, self.update_motor)

        self._robot_manager.on(RobotEvent.ERROR, self.report_errors_in_queue)

    def update_program_status(self, button_id, status: ScriptEvent):
        # log(f'program status update: {button_id} {status}')
        self._live.update_program_status(button_id, status)

    def update_motor(self, ref, motor_angles: List[int]) -> None:
        """Currently unused, as we are not doing anything with it in the app."""
        for angle, index in enumerate(motor_angles):
            self._live.update_motor(index, MotorData(0, 0, angle))

    def _on_connected(self, c) -> None:
        """On new INCOMING connection, update the callback interfaces."""
        self._log(f"BLE interface connected! {c}")
        self._robot_manager.on_connected(c)
        self.report_errors_in_queue()

    def _on_disconnect(self, *args) -> None:
        """When ble drops connection, call the robot manager's disconnect handler"""
        self._log("BLE interface disconnected!")
        self._robot_manager.on_disconnected()

    def disconnect(self) -> None:
        """When robot wants to disconnect."""
        self._bleno.disconnect()

    def __getitem__(self, item) -> BlenoPrimaryService:
        return self._named_services[item]

    ### We do not support this yet!
    # def _device_name_changed(self, name):
    #     os.environ["BLENO_DEVICE_NAME"] = name
    #     self._bleno.stopAdvertising(self._start_advertising)

    def _on_state_change(self, state: str):
        """When Bluetooth comes online, we get state changes."""
        self._log(f"on -> stateChange: {state}")

        if state == "poweredOn":
            self._start_advertising()
        else:
            self._bleno.stopAdvertising()

    def _start_advertising(self) -> None:
        """This is what makes the app find the robot"""
        self._log(f"Start advertising as {get_device_name()}")
        self._bleno.startAdvertising(get_device_name(), self._advertised_uuid_list)

    def _on_advertising_start(self, error) -> None:
        """Callback of self._bleno.startAdvertising"""

        def _result(result) -> str:
            return f"error {result}" if result else "success"

        self._log(f"on -> advertisingStart: {_result(error)}")

        if not error:

            def on_set_service_error(error) -> None:
                self._log(f"setServices: {_result(error)}")

            self._bleno.setServices(list(self._named_services.values()), on_set_service_error)

    def start(self) -> None:
        """Switch interface on, start the robot."""

        def service_status(service: str) -> int:
            bluetooth_status = subprocess.run(
                ["/usr/bin/systemctl", "status", service],
                capture_output=True,
                check=False,
            )

            self._log(f"Bluetooth status: {bluetooth_status.returncode}", LogLevel.INFO)

            return bluetooth_status.returncode

        # the old service descriptor contained a circular dependency, which means systemd
        # started up dependencies in a different order than we expected. This caused the
        # bluetooth service to not be started when we tried to start the revvy service.
        with open("/etc/systemd/system/revvy.service", "r") as f:
            is_old_image = (
                "Wants=bluetooth.target network.target sound.target hciuart.service dhcpcd.service systemd-logind.service dbus.service"
                in f.read()
            )

        if is_old_image:
            service = "bluetooth.service"
        else:
            service = "bluetooth.target"

        if service_status(service) != 0:
            self._log("Bluetooth service not running, waiting for it to start")
            stopwatch = Stopwatch()
            timeout = True
            while stopwatch.elapsed < 10:
                if service_status(service) == 0:
                    timeout = False
                    break
            if timeout:
                raise TimeoutError("Bluetooth service did not start in time, exiting")

        if is_old_image or is_rpi_zero_2w():
            # On older images, the systemd services were not properly ordered, so we need to wait
            # for the bluetooth service to start. This wait is a bit longer than measured startup
            # time of bluetooth.service. For some reason systemd immediately reports the service as
            # started, but it takes a bit longer for the bluetooth functionality to be available.
            #
            # The Raspberry Pi Zero W2, the whole stack seems to be sensitive of the SD card,
            # and delaying a bit more seems to help. It is also faster so we can tolerate the
            # delay.
            # Trying to use BLE immediately will result in an `OSError: [Errno 100] Network is down`
            time.sleep(1.5)

        self._bleno.start()
        self._robot_manager.robot_start()

    def stop(self) -> None:
        """Quit the program"""
        self._bleno.stopAdvertising()
        self._bleno.disconnect()

    def report_errors_in_queue(self, *args) -> None:
        while revvy_error_handler.has_error():
            self._live.report_error(revvy_error_handler.pop_error())


def is_rpi_zero_2w() -> bool:
    """Check if the device is a Raspberry Pi Zero 2 W"""
    with open("/proc/cpuinfo") as f:
        return "Raspberry Pi Zero 2 W" in f.read()

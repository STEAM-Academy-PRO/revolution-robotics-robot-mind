""" Bluetooth Low Energy interface for Revvy """

import os
import subprocess
from typing import Callable
from pybleno import Bleno, BlenoPrimaryService

from revvy.bluetooth.services.battery import CustomBatteryService
from revvy.bluetooth.services.device_information import DeviceInformationService
from revvy.bluetooth.services.long_message import LongMessageService
from revvy.robot.robot_events import RobotEvent

from revvy.utils.device_name import get_device_name
from revvy.utils.directories import BLE_STORAGE_DIR, WRITEABLE_ASSETS_DIR
from revvy.utils.logger import get_logger
from revvy.utils.file_storage import FileStorage, MemoryStorage

from revvy.robot_manager import RobotManager

from revvy.bluetooth.longmessage import LongMessageHandler, LongMessageStorage
from revvy.bluetooth.longmessage import extract_asset_longmessage, LongMessageImplementation

from revvy.bluetooth.live_message_service import LiveMessageService

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

        initial_battery_state = self._robot_manager._robot_state._battery.get()

        self._dis = DeviceInformationService()
        self._bas = CustomBatteryService(initial_battery_state)
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
        self._bleno.on("stateChange", self._on_state_change)
        self._bleno.on("advertisingStart", self._on_advertising_start)
        self._bleno.on("accept", self._on_connected)
        self._bleno.on("disconnect", self._on_disconnect)

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
        self._robot_manager.on(RobotEvent.SENSOR_VALUE_CHANGE, self._live.update_sensor)

        # Only send up ORIENTATION changes, NO GYRO as we are not using that anywhere.
        self._robot_manager.on(RobotEvent.ORIENTATION_CHANGE, self._live.update_orientation)
        self._robot_manager.on(RobotEvent.DISCONNECT, self.disconnect)
        self._robot_manager.on(RobotEvent.SESSION_ID_CHANGE, self._live.update_session_id)
        self._robot_manager.on(
            RobotEvent.SCRIPT_VARIABLE_CHANGE, self._live.update_script_variables
        )
        self._robot_manager.on(RobotEvent.PROGRAM_STATUS_CHANGE, self._live.update_program_status)
        self._robot_manager.on(
            RobotEvent.BACKGROUND_CONTROL_STATE_CHANGE, self._live.update_state_control
        )
        self._robot_manager.on(RobotEvent.TIMER_TICK, self._live.update_timer)
        self._robot_manager.on(RobotEvent.ERROR, self.report_errors_in_queue)
        self._robot_manager.on(RobotEvent.SESSION_ID_CHANGE, self._live.reset)

    def _on_connected(self, c) -> None:
        """On new INCOMING connection, update the callback interfaces."""
        self._log(f"BLE interface connected! {c}")
        self._robot_manager.on_connected(c)
        self.report_errors_in_queue()

    def _on_disconnect(self, *args) -> None:
        """When ble drops connection, call the robot manager's disconnect handler"""
        self._log("BLE interface disconnected!")
        self._robot_manager.on_disconnected()

    def disconnect(self, *args) -> None:
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

        def service_running() -> bool:
            bluetooth_status = subprocess.run(
                ["/usr/bin/systemctl", "status", "bluetooth.service"],
                capture_output=True,
                check=False,
            )

            return bluetooth_status.returncode == 0

        def hci_up() -> bool:
            hci_process = subprocess.run(
                ["/usr/bin/hciconfig", "hci0"],
                capture_output=True,
                check=False,
            )
            output = hci_process.stdout.__str__()

            return "UP RUNNING" in output

        def wait_for(check: Callable, name: str):
            if not check():
                self._log(f"Waiting for {name}")
                stopwatch = Stopwatch()
                timeout = True
                while stopwatch.elapsed < 10:
                    if check():
                        timeout = False
                        break
                if timeout:
                    raise TimeoutError(f"{name} did not start in time, exiting")

        wait_for(service_running, "Bluetooth service")
        wait_for(hci_up, "HCI interface")

        self._bleno.start()

    def stop(self) -> None:
        """Quit the program"""
        self._bleno.stopAdvertising()
        self._bleno.disconnect()

    def report_errors_in_queue(self, *args) -> None:
        while revvy_error_handler.has_error():
            self._live.report_error(revvy_error_handler.pop_error())

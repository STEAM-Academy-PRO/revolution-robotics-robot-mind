""" Bluetooth Low Energy interface for Revvy """

import os
from typing import List
from pybleno import Bleno
from revvy.bluetooth.ble_characteristics import GyroData

from revvy.bluetooth.services.battery import CustomBatteryService
from revvy.bluetooth.services.device_information import DeviceInformationService
from revvy.bluetooth.services.long_message import LongMessageService
from revvy.robot.robot_events import RobotEvent
from revvy.scripting.runtime import ScriptEvent

from revvy.utils.device_name import get_device_name
from revvy.utils.directories import BLE_STORAGE_DIR, WRITEABLE_ASSETS_DIR
from revvy.utils.logger import get_logger
from revvy.utils.file_storage import FileStorage, MemoryStorage

from revvy.robot_manager import RobotManager

from revvy.bluetooth.longmessage import LongMessageHandler, LongMessageStorage
from revvy.bluetooth.longmessage import extract_asset_longmessage, LongMessageImplementation

from revvy.bluetooth.live_message_service import LiveMessageService, MotorData

from revvy.utils.error_reporter import compress_error, revvy_error_handler

log = get_logger("BLE")


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
        self.long_message_handler = LongMessageHandler(long_message_storage)

        lmi = LongMessageImplementation(robot_manager, long_message_storage, WRITEABLE_ASSETS_DIR)
        self.long_message_handler.on_upload_started(lmi.on_upload_started)
        self.long_message_handler.on_upload_progress(lmi.on_upload_progress)
        self.long_message_handler.on_upload_finished(lmi.on_transmission_finished)
        self.long_message_handler.on_message_updated(lmi.on_message_updated)

        ### -----------------------------------------------------
        ### Services
        ### -----------------------------------------------------

        self._dis = DeviceInformationService()
        self._bas = CustomBatteryService()
        self._live = LiveMessageService(robot_manager)
        self._long = LongMessageService(self.long_message_handler)

        self._named_services = {
            "device_information_service": self._dis,
            "battery_service": self._bas,
            "long_message_service": self._long,
            "live_message_service": self._live,
        }

        self._advertised_uuid_list = [self._live["uuid"]]

        self._bleno = Bleno()

        # _bleno exposes it's on function runtime, which makes the linter sad.
        self._bleno.on(
            "stateChange", self._on_state_change
        )  # pyright: ignore[reportAttributeAccessIssue]
        self._bleno.on(
            "advertisingStart", self._on_advertising_start
        )  # pyright: ignore[reportAttributeAccessIssue]
        self._bleno.on("accept", self._on_connected)  # pyright: ignore[reportAttributeAccessIssue]
        self._bleno.on(
            "disconnect", self._on_disconnect
        )  # pyright: ignore[reportAttributeAccessIssue]

        self.subscribe_to_state_changes()

    def subscribe_to_state_changes(self) -> None:
        """
        Use the event emitter pattern to subscribe to robot status changes
        The robot manager will emit everything we need to communicate back
        to the mobile app.
        """

        self._robot_manager.on(
            RobotEvent.BATTERY_CHANGE,
            lambda ref, val: self._bas.characteristic("unified_battery_status").update_value(val),
        )

        # Initialize value - this could be prettier, not sure how yet.
        initial_battery_state = self._robot_manager._robot_state._battery.get()
        log(f"initial battery state {initial_battery_state}")
        self._bas.characteristic("unified_battery_status").update_value(initial_battery_state)

        self._robot_manager.on(
            RobotEvent.SENSOR_VALUE_CHANGE,
            lambda ref, sensor_reading: self._live.update_sensor(
                sensor_reading.id, sensor_reading.raw_value
            ),
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

    def update_motor(self, ref, motor_angles: List[int]):
        """Currently unused, as we are not doing anything with it in the app."""
        for angle, index in enumerate(motor_angles):
            self._live.update_motor(index, MotorData(0, 0, angle))

    def _on_connected(self, c):
        """On new INCOMING connection, update the callback interfaces."""
        log(f"BLE interface connected! {c}")
        self._robot_manager.on_connected(c)
        self.report_errors_in_queue()

    def _on_disconnect(self, *args):
        """When ble drops connection, call the robot manager's disconnect handler"""
        log("BLE interface disconnected!")
        self._robot_manager.on_disconnected()

    def disconnect(self):
        """When robot wants to disconnect."""
        self._bleno.disconnect()

    def __getitem__(self, item):
        return self._named_services[item]

    ### We do not support this yet!
    # def _device_name_changed(self, name):
    #     os.environ["BLENO_DEVICE_NAME"] = name
    #     self._bleno.stopAdvertising(self._start_advertising)

    def _on_state_change(self, state):
        """When Bluetooth comes online, we get state changes."""
        self._log(f"on -> stateChange: {state}")

        if state == "poweredOn":
            self._start_advertising()
        else:
            self._bleno.stopAdvertising()

    def _start_advertising(self):
        """This is what makes the app find the robot"""
        self._log("Start advertising as {}".format(get_device_name()))
        self._bleno.startAdvertising(get_device_name(), self._advertised_uuid_list)

    def _on_advertising_start(self, error):
        """Callback of self._bleno.startAdvertising"""

        def _result(result):
            return "error " + str(result) if result else "success"

        self._log(f"on -> advertisingStart: {_result(error)}")

        if not error:

            def on_set_service_error(error):
                self._log(f"setServices: {_result(error)}")

            self._bleno.setServices(list(self._named_services.values()), on_set_service_error)

    def start(self):
        """Switch interface on, start the robot."""
        self._bleno.start()
        self._robot_manager.robot_start()

    def stop(self):
        """Quit the program"""
        self._bleno.stopAdvertising()
        self._bleno.disconnect()

    def report_errors_in_queue(self, *args):
        """In case of an error, send it slow!"""
        while revvy_error_handler.has_error():
            self._live._error_reporting_characteristic.send_queued(
                compress_error(revvy_error_handler.pop_error())
            )

# SPDX-License-Identifier: GPL-3.0-only

import os


from pybleno import Bleno
from revvy.bluetooth.services.battery import CustomBatteryService

from revvy.bluetooth.services.device_information import DeviceInformationService
from revvy.bluetooth.services.long_message import LongMessageService
from revvy.utils.logger import get_logger
from revvy.utils.file_storage import FileStorage, MemoryStorage
from revvy.utils.observable import Observable

from revvy.robot.communication import RobotCommunicationInterface
from revvy.robot_manager import RobotManager

from revvy.bluetooth.longmessage import LongMessageHandler, LongMessageStorage
from revvy.bluetooth.longmessage import extract_asset_longmessage, LongMessageImplementation

from revvy.bluetooth.live_message_service import LiveMessageService

log = get_logger("BLE")


class RevvyBLE(RobotCommunicationInterface):
    """
    Revvy Bluetooth Interface

    Listens to connections from the app and controls the robot.
    """
    def __init__(self, robot_manager: RobotManager, device_name: Observable, serial, writeable_data_dir, writeable_assets_dir):
        self._deviceName = device_name.get()
        self._robot_manager = robot_manager

        self._log = get_logger('RevvyBLE')
        os.environ["BLENO_DEVICE_NAME"] = self._deviceName
        self._log(f'Initializing BLE with device name {self._deviceName}')

        device_name.subscribe(self._device_name_changed)


        ### -----------------------------------------------------
        ### Long Message Handler for receiving files and configs.
        ### -----------------------------------------------------

        ble_storage_dir = os.path.join(writeable_data_dir, 'ble')

        ble_storage = FileStorage(ble_storage_dir)

        long_message_storage = LongMessageStorage(ble_storage, MemoryStorage())
        extract_asset_longmessage(long_message_storage, writeable_assets_dir)
        self.long_message_handler = LongMessageHandler(long_message_storage)

        lmi = LongMessageImplementation(robot_manager, long_message_storage, writeable_assets_dir, False)
        self.long_message_handler.on_upload_started(lmi.on_upload_started)
        self.long_message_handler.on_upload_progress(lmi.on_upload_progress)
        self.long_message_handler.on_upload_finished(lmi.on_transmission_finished)
        self.long_message_handler.on_message_updated(lmi.on_message_updated)

        ### -----------------------------------------------------
        ### Services
        ### -----------------------------------------------------


        self._dis = DeviceInformationService(device_name, serial)
        self._bas = CustomBatteryService()
        self._live = LiveMessageService(robot_manager)
        self._long = LongMessageService(self.long_message_handler)


        self._named_services = {
            'device_information_service': self._dis,
            'battery_service': self._bas,
            'long_message_service': self._long,
            'live_message_service': self._live
        }

        self._advertised_uuid_list = [
            self._live['uuid']
        ]

        self._bleno = Bleno()
        self._bleno.on('stateChange', self._on_state_change)
        self._bleno.on('advertisingStart', self._on_advertising_start)
        self._bleno.on('accept', lambda _: self._robot_manager.on_connection_changed(True))
        self._bleno.on('disconnect', lambda _: self._robot_manager.on_connection_changed(False))

        self._robot_manager.set_communication_interface_callbacks(self)


    def __getitem__(self, item):
        return self._named_services[item]

    def _device_name_changed(self, name):
        self._deviceName = name
        os.environ["BLENO_DEVICE_NAME"] = self._deviceName
        self._bleno.stopAdvertising(self._start_advertising)

    def _on_state_change(self, state):
        self._log(f'on -> stateChange: {state}')

        if state == 'poweredOn':
            self._start_advertising()
        else:
            self._bleno.stopAdvertising()

    def _start_advertising(self):
        self._log('Start advertising as {}'.format(self._deviceName))
        self._bleno.startAdvertising(self._deviceName, self._advertised_uuid_list)

    def _on_advertising_start(self, error):
        def _result(result):
            return "error " + str(result) if result else "success"

        self._log(f'on -> advertisingStart: {_result(error)}')

        if not error:
            # noinspection PyShadowingNames
            def on_set_service_error(error):
                self._log(f'setServices: {_result(error)}')

            self._bleno.setServices(list(self._named_services.values()), on_set_service_error)

    def start(self):
        self._bleno.start()
        self._robot_manager.robot_start()

    def stop(self):
        self._bleno.stopAdvertising()
        self._bleno.disconnect()

    def update_session_id(self, id):
        return self._live.update_session_id(id)

    def update_orientation(self, vector_orientation):
        return self._live.update_orientation(vector_orientation)


    def update_gyro(self, vector_list):
        return self._live.update_gyro(vector_list)

    def update_motor(self, id, power, speed, pos):
        return self._live.update_motor(id, power, speed, pos)

    def update_sensor(self, id, raw_value):
        return self._live.update_sensor(id, raw_value)

    def update_script_variable(self, script_variables):
        return self._live.update_script_variable(script_variables)

    def update_state_control(self, control_state):
        return self._live.update_state_control(control_state)

    def update_timer(self, time):
        return self._live.update_timer(time)

    def update_characteristic(self, name, value):
        return self._dis.characteristic(name).update(value)

    def battery(self, name):
        return self._bas.characteristic(name)
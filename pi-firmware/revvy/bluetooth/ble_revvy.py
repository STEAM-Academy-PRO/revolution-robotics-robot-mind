# SPDX-License-Identifier: GPL-3.0-only

import os
import struct
import traceback

from pybleno import Bleno, BlenoPrimaryService, Characteristic, Descriptor

from revvy.utils.functions import bits_to_bool_list
from revvy.utils.logger import get_logger, LogLevel
from revvy.utils.logger import get_logger
from revvy.utils.file_storage import FileStorage, MemoryStorage

from revvy.robot.remote_controller import RemoteControllerCommand
from revvy.robot.communication import RobotCommunicationInterface
from revvy.robot_manager import RobotManager, RevvyStatusCode

from revvy.bluetooth.longmessage import LongMessageError, LongMessageProtocol
from revvy.bluetooth.longmessage import LongMessageHandler, LongMessageStorage
from revvy.bluetooth.longmessage import extract_asset_longmessage, LongMessageImplementation

log = get_logger("BLE")

class BleService(BlenoPrimaryService, RobotCommunicationInterface):
    def __init__(self, uuid, characteristics: dict):

        self._named_characteristics = characteristics

        super().__init__({
            'uuid':            uuid,
            'characteristics': list(characteristics.values())
        })

    def characteristic(self, item):
        return self._named_characteristics[item]


class Observable:
    def __init__(self, value):
        self._value = value
        self._observers = []

    def update(self, value):
        self._value = value
        self._notify_observers(value)

    def get(self):
        return self._value

    def subscribe(self, observer):
        self._observers.append(observer)

    def unsubscribe(self, observer):
        self._observers.remove(observer)

    def _notify_observers(self, new_value):
        for observer in self._observers:
            observer(new_value)


# Device communication related services


class LongMessageCharacteristic(Characteristic):
    def __init__(self, handler):
        super().__init__({
            'uuid':       'd59bb321-7218-4fb9-abac-2f6814f31a4d',
            'properties': ['read', 'write'],
            'value':      None
        })
        self._handler = LongMessageProtocol(handler)

    def onReadRequest(self, offset, callback):
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG)
        else:
            try:
                value = self._handler.handle_read()
                callback(Characteristic.RESULT_SUCCESS, value)

            except LongMessageError:
                callback(Characteristic.RESULT_UNLIKELY_ERROR, None)

    @staticmethod
    def _translate_result(result):
        if result == LongMessageProtocol.RESULT_SUCCESS:
            return Characteristic.RESULT_SUCCESS
        elif result == LongMessageProtocol.RESULT_INVALID_ATTRIBUTE_LENGTH:
            return Characteristic.RESULT_INVALID_ATTRIBUTE_LENGTH
        else:
            return Characteristic.RESULT_UNLIKELY_ERROR

    def onWriteRequest(self, data, offset, without_response, callback):
        result = Characteristic.RESULT_UNLIKELY_ERROR
        try:
            if offset:
                result = Characteristic.RESULT_ATTR_NOT_LONG

            elif len(data) < 1:
                result = Characteristic.RESULT_INVALID_ATTRIBUTE_LENGTH

            else:
                result = self._translate_result(self._handler.handle_write(data[0], data[1:]))

        except LongMessageError:
            log(traceback.format_exc())
        finally:
            callback(result)


class LongMessageService(BlenoPrimaryService):
    def __init__(self, handler):
        super().__init__({
            'uuid':            '97148a03-5b9d-11e9-8647-d663bd873d93',
            'characteristics': [
                LongMessageCharacteristic(handler),
            ]})

VALIDATE_CONFIG_STATE_UNKNOWN = 0
VALIDATE_CONFIG_STATE_IN_PROGRESS = 1
VALIDATE_CONFIG_STATE_DONE = 2
NUM_MOTOR_PORTS = 6
NUM_SENSOR_PORTS = 4

class ValidateConfigCharacteristic(Characteristic):
    def __init__(self, uuid, description, callback):
        self._on_write_callback = callback
        self._value = struct.pack('<I', 0)
        self._state = VALIDATE_CONFIG_STATE_UNKNOWN
        super().__init__({
            'uuid':        uuid,
            'properties':  ['write', 'read'],
            'value':       None,
            'descriptors': [
                Descriptor({
                    'uuid':  '2901',
                    'value': description
                }),
            ]
        })

    def onWriteRequest(self, data, offset, without_response, callback):
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG)
        elif len(data) != 7:
            log('validate_config::onWriteRequest::wrong length')
            callback(Characteristic.RESULT_INVALID_ATTRIBUTE_LENGTH)
        elif self._on_write_callback(data):
            callback(Characteristic.RESULT_SUCCESS)
        else:
            callback(Characteristic.RESULT_UNLIKELY_ERROR)

    def onReadRequest(self, offset, callback):
        log('validate_config::onReadRequest')
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG, None)
        else:
            callback(Characteristic.RESULT_SUCCESS, self._value)

    def get_state(self):
        return self._state

    def update_validate_config_result(self, state, motors_bitmask, sensor0, sensor1,
        sensor2, sensor3):

        self._state = state
        self._value = struct.pack('BBBBBB', state, motors_bitmask, sensor0,
            sensor1, sensor2, sensor3)

        log('validate_config::update:', self._value)


class MobileToBrainFunctionCharacteristic(Characteristic):
    def __init__(self, uuid, min_length, max_length, description, callback):
        self._callbackFn = callback
        self._minLength = min_length
        self._maxLength = max_length
        self._value = struct.pack('<I', 0)
        super().__init__({
            'uuid':        uuid,
            'properties':  ['write', 'read', 'notify'],
            'value':       None,
            'descriptors': [
                Descriptor({
                    'uuid':  '2901',
                    'value': description
                }),
            ]
        })
        self._update_value_callback = None

    def onWriteRequest(self, data, offset, without_response, callback):
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG)
        elif not (self._minLength <= len(data) <= self._maxLength):
            callback(Characteristic.RESULT_INVALID_ATTRIBUTE_LENGTH)
        elif self._callbackFn(data):
            callback(Characteristic.RESULT_SUCCESS)
        else:
            callback(Characteristic.RESULT_UNLIKELY_ERROR)

    def onReadRequest(self, offset, callback):
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG, None)
        else:
            callback(Characteristic.RESULT_SUCCESS, self._value)

    def onSubscribe(self, max_value_size, update_value_callback):
        self._update_value_callback = update_value_callback

    def onUnsubscribe(self):
        self._update_value_callback = None

    def update(self, value):
        self._value = value

        if self._update_value_callback:
            self._update_value_callback(value)


class BrainToMobileFunctionCharacteristic(Characteristic):
    def __init__(self, uuid, description):
        self._value = []
        self._updateValueCallback = None
        super().__init__({
            'uuid':        uuid,
            'properties':  ['read', 'notify'],
            'value':       None,
            'descriptors': [
                Descriptor({
                    'uuid':  '2901',
                    'value': description
                }),
            ]
        })

    def onReadRequest(self, offset, callback):
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG, None)
        else:
            callback(Characteristic.RESULT_SUCCESS, self._value)

    def onSubscribe(self, max_value_size, update_value_callback):
        self._updateValueCallback = update_value_callback

    def onUnsubscribe(self):
        self._updateValueCallback = None

    def update(self, value):
        self._value = value

        callback = self._updateValueCallback
        if callback:
            callback(value)


class RelativeFunctionCharacteristic(Characteristic):
    def __init__(self, uuid, description, callback):
        self._value = []
        self._updateValueCallback = None
        self._callbackFn = callback
        super().__init__({
            'uuid': uuid,
            'properties': ['read', 'notify', 'write'],
            'value': None,
            'descriptors': [
                Descriptor({
                    'uuid': '2901',
                    'value': description
                }),
            ]
        })

    def onReadRequest(self, offset, callback):
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG, None)
        else:
            callback(Characteristic.RESULT_SUCCESS, self._value)

    def onSubscribe(self, max_value_size, update_value_callback):
        self._updateValueCallback = update_value_callback

    def onUnsubscribe(self):
        self._updateValueCallback = None

    def update(self, value):
        self._value = value

        callback = self._updateValueCallback
        if callback:
            callback(value)

    def onWriteRequest(self, data, offset, without_response, callback):
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG)
        # elif not (self._minLength <= len(data) <= self._maxLength):
        #     callback(Characteristic.RESULT_INVALID_ATTRIBUTE_LENGTH)
        elif self._callbackFn(data):
            callback(Characteristic.RESULT_SUCCESS)
        else:
            callback(Characteristic.RESULT_UNLIKELY_ERROR)

class StateControlCharacteristic(RelativeFunctionCharacteristic):
    pass

class SensorCharacteristic(BrainToMobileFunctionCharacteristic):
    def update(self, value):
        # FIXME: prefix with data length is probably unnecessary
        super().update([len(value), *value])


class MotorCharacteristic(BrainToMobileFunctionCharacteristic):
    pass


class GyroCharacteristic(BrainToMobileFunctionCharacteristic):
    pass

class TimerCharacteristic(BrainToMobileFunctionCharacteristic):
    pass


class ReadVariableCharacteristic(BrainToMobileFunctionCharacteristic):
    pass


class LiveMessageService(BlenoPrimaryService):
    def __init__(self):
        self._message_handler = None
        self.__validate_config_req_cb = None

        # on_joystick_action is a callback that should run when LiveMessageService
        # detects that joystick action is received from mobile app over a curtain
        # characteristic
        self.__joystick_action_cb = None

        self._read_variable_characteristic = [
            ReadVariableCharacteristic('d4ad2a7b-57be-4803-8df0-6807073961ad', b'Variable Slots')
        ]

        self._gyro_characteristic = [
            GyroCharacteristic('d5bd4300-7c49-4108-8500-8716ffd39de8', b'Gyro'),
        ]

        self._orientation_characteristic = [
            GyroCharacteristic('4337a7c2-cae9-4c88-8908-8810ee013fcb', b'Orientation')
        ]

        self._timer_characteristic = [
            TimerCharacteristic('c0e913da-5fdd-4a17-90b4-47758d449306', b'Timer'),
        ]

        self._state_control_characteristic = [
            RelativeFunctionCharacteristic(
                '53881a54-d519-40f7-8cbf-d43ced67f315', b'State Control', self.state_control_callback
            )
        ]

        self._sensor_characteristics = [
            SensorCharacteristic('135032e6-3e86-404f-b0a9-953fd46dcb17', b'Sensor 1'),
            SensorCharacteristic('36e944ef-34fe-4de2-9310-394d482e20e6', b'Sensor 2'),
            SensorCharacteristic('b3a71566-9af2-4c9d-bc4a-6f754ab6fcf0', b'Sensor 3'),
            SensorCharacteristic('9ace575c-0b70-4ed5-96f1-979a8eadbc6b', b'Sensor 4'),
        ]

        self._motor_characteristics = [
            MotorCharacteristic('4bdfb409-93cc-433a-83bd-7f4f8e7eaf54', b'Motor 1'),
            MotorCharacteristic('454885b9-c9d1-4988-9893-a0437d5e6e9f', b'Motor 2'),
            MotorCharacteristic('00fcd93b-0c3c-4940-aac1-b4c21fac3420', b'Motor 3'),
            MotorCharacteristic('49aaeaa4-bb74-4f84-aa8f-acf46e5cf922', b'Motor 4'),
            MotorCharacteristic('ceea8e45-5ff9-4325-be13-48cf40c0e0c3', b'Motor 5'),
            MotorCharacteristic('8e4c474f-188e-4d2a-910a-cf66f674f569', b'Motor 6'),
        ]

        self._mobile_to_brain = MobileToBrainFunctionCharacteristic(
            '7486bec3-bb6b-4abd-a9ca-20adc281a0a4', 20, 20, b'simpleControl',
             self.simple_control_callback)

        self._validate_config_charateristic = ValidateConfigCharacteristic(
            'ad635567-07a7-4c8a-8765-d504dac7c86f', b'Validate configuration',
             self.validate_config_callback)

        self._buf_gyro = b'\xff'
        self._buf_orientation = b'\xff'
        self._buf_script_variables = b'\xff'
        self._buf_timer = b'\xff'

        super().__init__({
            'uuid':            'd2d5558c-5b9d-11e9-8647-d663bd873d93',
            'characteristics': [self._mobile_to_brain,
                self._validate_config_charateristic,
                *self._sensor_characteristics,
                *self._motor_characteristics,
                *self._gyro_characteristic,
                *self._orientation_characteristic,
                *self._read_variable_characteristic,
                *self._state_control_characteristic,
                *self._timer_characteristic,
            ]
        })

    def set_periodic_control_msg_cb(self, callback):
        self.__periodic_control_msg_cb = callback

    def set_joystick_action_cb(self, callback):
        self.__joystick_action_cb = callback

    def set_validate_config_req_cb(self, callback):
        self.__validate_config_req_cb = callback

    def validate_config_callback(self, data):
        motor_bitmask, sensor0, sensor1, sensor2, sensor3, \
        motor_load_power, threshold = \
            struct.unpack('BBBBBBB', data)

        current_state = self._validate_config_charateristic.get_state()
        if current_state == VALIDATE_CONFIG_STATE_IN_PROGRESS:
            return False

        motors = [(motor_bitmask >> i) & 1 for i in range(NUM_MOTOR_PORTS)]

        fn = self.__validate_config_req_cb
        fn(motors, [sensor0, sensor1, sensor2, sensor3], motor_load_power,
            threshold)

        self._validate_config_charateristic.update_validate_config_result(
          VALIDATE_CONFIG_STATE_IN_PROGRESS, motor_bitmask, sensor0, sensor1,
          sensor2, sensor3)

        return True

    def set_validation_result(self, success: bool,
        motors: list, sensors: list):

        valitation_state = VALIDATE_CONFIG_STATE_UNKNOWN
        if success:
            valitation_state = VALIDATE_CONFIG_STATE_DONE

        if len(motors) != NUM_MOTOR_PORTS:
            log('set_validation_result::invalid motors response: ', motors)

        motor_bitmask = 0
        for i in range(max(NUM_MOTOR_PORTS, len(motors))):
            motor_bit = 0
            if isinstance(motors[i], bool):
                motor_bit = motors[i]
            motor_bitmask |= motor_bit << i

        if len(sensors) == NUM_SENSOR_PORTS:
            s0, s1, s2, s3 = sensors
        else:
            s0 = s1 = s2 = s3 = False

        self._validate_config_charateristic.update_validate_config_result(
          valitation_state, motor_bitmask, s0, s1, s2, s3)


    def simple_control_callback(self, data):
        # Simple control callback is run each time new controller data
        # representing full state of joystick is sent over a BLE characteristic
        # Analog values: X and Y axes of a joystick, mapped to 0-255, where 127
        # is the middle value representing joystick axis in neutral state.

        def joystick_axis_is_neutral(value):
            # value is in 1 byte range 0-255, with 127 being the middle position
            # of a joystick along that axis
            return value == 127

        def joystick_xy_is_moved(analog_values):
            if len(analog_values) < 2:
                return False

            x_value = analog_values[0]
            y_value = analog_values[1]
            for v in [x_value, y_value]:
                if not joystick_axis_is_neutral(v):
                    return True
            return False

        analog_values = data[1:7]
        deadline_packed = data[7:11]
        next_deadline = struct.unpack('<I', deadline_packed)[0]
        button_values = bits_to_bool_list(data[11:15])

        joystick_xy_action = joystick_xy_is_moved(analog_values)
        joystick_button_action = any(button_values)

        # First user input action triggers global timer
        if joystick_xy_action or joystick_button_action:
            self.__joystick_action_cb()

        message_handler = self.__periodic_control_msg_cb
        if message_handler:
            message_handler(RemoteControllerCommand(analog=analog_values,
                                                    buttons=button_values,
                                                    background_command=None,
                                                    next_deadline=next_deadline))
        return True

    def state_control_callback(self, data):
        background_control_command = int.from_bytes(data[2:], byteorder='big')
        message_handler = self.__periodic_control_msg_cb
        if message_handler:
            message_handler(RemoteControllerCommand(analog=b'\x7f\x7f\x00\x00\x00\x00\x00\x00\x00\x00',
                                                    buttons=[False]*32,
                                                    background_command=background_control_command,
                                                    next_deadline=None))
        return True

    def update_sensor(self, sensor, value):
        if 0 < sensor <= len(self._sensor_characteristics):
            self._sensor_characteristics[sensor - 1].update(value)

    def update_motor(self, motor, power, speed, position):
        if 0 < motor <= len(self._motor_characteristics):
            data = list(struct.pack(">flb", speed, position, power))
            self._motor_characteristics[motor - 1].update(data)

    def update_session_id(self, value):
        log('update_session_id:' + str(value))
        data = list(struct.pack('<I', value))
        self._mobile_to_brain.update(data)

    def update_gyro(self, vector_list):
        if type(vector_list) is list:
            buf = struct.pack('%sf' % len(vector_list), *vector_list)
            if self._buf_gyro is not buf:
                self._buf_gyro = buf
                self._gyro_characteristic[0].update(self._buf_gyro)

    def update_orientation(self, vector_list):
        if type(vector_list) is list:
            buf = struct.pack('%sf' % len(vector_list), *vector_list)
            if self._buf_orientation is not buf:
                self._buf_orientation = buf
                self._orientation_characteristic[0].update(self._buf_orientation)

    def update_timer(self, data):
        buf = list(struct.pack(">bf", 4, data))
        if self._buf_timer != buf:
            self._buf_timer = buf
            self._timer_characteristic[0].update(self._buf_timer)

    def update_script_variable(self, script_variables):
        # By characteristic protocol - maximum slots in BLE message is 4
        MAX_VARIABLE_SLOTS = 4

        # Message format:
        # offset:  0    1  2  3  4    5  6  7  8    9  10 11 12   13 14 15 16
        # values:  0A | BB BB BB BB | CC CC CC CC | DD DD DD DD | EE EE EE EE
        # A - bitmask consists of 4 bits. if bit is set - value has been set
        #     by scripts. If bit is not set - value has never been changed yet,
        #     due to script not run at all, or script has not yet set the value
        #     and ReportVariableChanged has not been called for this slot

        # BB - float value for Slot 1
        # CC - float value for Slot 2
        # DD - float value for Slot 3
        # EE - float value for Slot 4

        # In the end the user of this packet receives info about 4 slots, current
        # value of each slot, has the value in this slot been set at least once

        mask = 0
        valuebuf = b''

        for slot_idx in range(MAX_VARIABLE_SLOTS):
            v = script_variables.get_variable(slot_idx)
            if v.is_valid() and v.value_is_set():
                value = v.get_value()
                mask = mask | (1 << slot_idx)
            else:
                value = 0.0
            valuebuf += struct.pack('f', value)

        maskbuf = struct.pack('B', mask)
        msg = maskbuf + valuebuf
        # log('scriptvars', msg)
        self._read_variable_characteristic[0].update(msg)

    def update_state_control(self, state):
        data = list(struct.pack(">bl", 4, state))
        self._state_control_characteristic[0].update(data)

# Device Information Service
class ReadOnlyCharacteristic(Characteristic):
    def __init__(self, uuid, value):
        super().__init__({
            'uuid':       uuid,
            'properties': ['read'],
            'value':      value
        })


class SerialNumberCharacteristic(ReadOnlyCharacteristic):
    def __init__(self, serial):
        super().__init__('2A25', serial.encode())


class ManufacturerNameCharacteristic(ReadOnlyCharacteristic):
    def __init__(self, name):
        super().__init__('2A29', name)


class ModelNumberCharacteristic(ReadOnlyCharacteristic):
    def __init__(self, model_no):
        super().__init__('2A24', model_no)


class VersionCharacteristic(Characteristic):
    version_max_length = 20

    def __init__(self, uuid):
        super().__init__({
            'uuid':       uuid,
            'properties': ['read'],
            'value':      None
        })
        self._version = []

    def onReadRequest(self, offset, callback):
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG, None)
        else:
            callback(Characteristic.RESULT_SUCCESS, self._version)

    def update(self, version):
        if len(version) > self.version_max_length:
            version = version[:self.version_max_length]
        self._version = version.encode("utf-8")


class SystemIdCharacteristic(Characteristic):
    def __init__(self, system_id: Observable):
        super().__init__({
            'uuid':       '2A23',
            'properties': ['read', 'write'],
            'value':      None
        })
        self._system_id = system_id

    def onReadRequest(self, offset, callback):
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG, None)
        else:
            callback(Characteristic.RESULT_SUCCESS, self._system_id.get().encode('utf-8'))

    def onWriteRequest(self, data, offset, without_response, callback):
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG)
        else:
            try:
                name = data.decode('ascii')
                if 0 < len(name) <= 15:
                    self._system_id.update(name)
                    callback(Characteristic.RESULT_SUCCESS)
                else:
                    callback(Characteristic.RESULT_UNLIKELY_ERROR)
            except UnicodeDecodeError:
                callback(Characteristic.RESULT_UNLIKELY_ERROR)


class RevvyDeviceInformationService(BleService):
    def __init__(self, device_name: Observable, serial):
        hw = VersionCharacteristic('2A27')
        fw = VersionCharacteristic('2A26')
        sw = VersionCharacteristic('2A28')
        serial = SerialNumberCharacteristic(serial)
        manufacturer_name = ManufacturerNameCharacteristic(b'RevolutionRobotics')
        model_number = ModelNumberCharacteristic(b'RevvyAlpha')
        system_id = SystemIdCharacteristic(device_name)

        super().__init__('180A', {
            'hw_version': hw,
            'fw_version': fw,
            'sw_version': sw,
            'serial_number': serial,
            'manufacturer_name': manufacturer_name,
            'model_number': model_number,
            'system_id': system_id
        })


class CustomBatteryLevelCharacteristic(Characteristic):
    """Custom battery service that contains 2 characteristics"""
    def __init__(self, uuid, description):
        super().__init__({
            'uuid':        uuid,
            'properties':  ['read', 'notify'],
            'value':       None,  # needs to be None because characteristic is not constant value
            'descriptors': [
                Descriptor({
                    'uuid':  '2901',
                    'value': description
                })
            ]
        })

        self._updateValueCallback = None
        self._value = 99  # initial value only

    def onReadRequest(self, offset, callback):
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG, None)
        else:
            callback(Characteristic.RESULT_SUCCESS, [self._value])

    def onSubscribe(self, max_value_size, update_value_callback):
        self._updateValueCallback = update_value_callback

    def onUnsubscribe(self):
        self._updateValueCallback = None

    def update_value(self, value):
        if self._value == value:   # don't update if there is no change
            return
        self._value = value

        update_value_callback = self._updateValueCallback
        if update_value_callback:
            update_value_callback([value])


class UnifiedBatteryInfoCharacteristic(CustomBatteryLevelCharacteristic):
    def onReadRequest(self, offset, callback):
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG, None)
        else:
            callback(Characteristic.RESULT_SUCCESS, self._value)

    def update_value(self,
        core_battery_level,
        core_battery_status,
        motor_battery_level,
        motor_battery_present):

        new_value = [
            core_battery_level,
            core_battery_status,
            motor_battery_level,
            motor_battery_present
        ]

        if new_value == self._value:
            return

        self._value = new_value

        if self._updateValueCallback:
            self._updateValueCallback(self._value)


class CustomBatteryService(BleService):
    def __init__(self):
        main_deprecated = CustomBatteryLevelCharacteristic('2A19', b'Main battery percentage')
        unified_battery_status = UnifiedBatteryInfoCharacteristic('2BED', b'Unified battery staus')
        motor = CustomBatteryLevelCharacteristic('00002a19-0000-1000-8000-00805f9b34fa', b'Motor battery percentage')

        super().__init__('180F', {
            'main_battery': main_deprecated,
            'unified_battery_status': unified_battery_status,
            'motor_battery': motor,
        })


class RevvyBLE:
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


        self._dis = RevvyDeviceInformationService(device_name, serial)
        self._bas = CustomBatteryService()
        self._live = LiveMessageService()
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

        self._robot_manager.set_control_interface_callbacks(self)


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
            self._log('setServices')

            # noinspection PyShadowingNames
            def on_set_service_error(error):
                self._log(f'setServices: {_result(error)}')

            self._bleno.setServices(list(self._named_services.values()), on_set_service_error)

    def on_connection_changed(self, callback):
        self._bleno.on('accept', lambda _: callback(True))
        self._bleno.on('disconnect', lambda _: callback(False))

    def start(self):
        self._bleno.start()
        self._robot_manager.robot_start()

    def stop(self):
        self._bleno.stopAdvertising()
        self._bleno.disconnect()


    def set_periodic_control_msg_cb(self, cb):
        return self._live.set_periodic_control_msg_cb(cb)

    def set_joystick_action_cb(self, cb):
        return self._live.set_joystick_action_cb(cb)

    def set_validate_config_req_cb(self, cb):
        return self._live.set_validate_config_req_cb(cb)


    def update_session_id(self, id):
        return self._live.update_session_id(id)

    def set_validation_result(self, success, motors, sensors):
        return self._live.set_validation_result(success, motors, sensors)

    def update_orientation(self, vector_orientation):
        return self._live.update_orientation(vector_orientation)


    def update_gyro(self, vector_list):
        return self._live.update_gyro(vector_list)

    def update_motor(self, id, power, speed, pos):
        return self._live.update_motor(id, power, speed, pos)

    def update_sensor(self, id, power, speed, pos):
        return self._live.update_sensor(id, power, speed, pos)

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
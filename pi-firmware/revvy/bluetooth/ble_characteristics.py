""" Define Bluetooth communication protocols """
import struct
import traceback

from pybleno import Characteristic, Descriptor
from revvy.bluetooth.validate_config_statuses import VALIDATE_CONFIG_STATE_UNKNOWN
from revvy.bluetooth.longmessage import LongMessageError, LongMessageProtocol
from revvy.mcu.commands import BatteryStatus
from revvy.utils.bit_packer import pack_2_bit_number_array_32, unpack_2_bit_number_array_32

from revvy.utils.logger import get_logger

log = get_logger("BLE Characteristics")

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

    def onWriteRequest(self, data, offset, withoutResponse, callback):
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

    def update_validate_config_result(self, state, motors_bitmask, sensors):

        self._state = state
        self._value = struct.pack('BBBBBB', state, motors_bitmask, sensors[0],
            sensors[1], sensors[2], sensors[3])

        log('validate_config::update:', self._value)




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

    def onSubscribe(self, maxValueSize, updateValueCallback):
        self._updateValueCallback = updateValueCallback

    def onUnsubscribe(self):
        self._updateValueCallback = None

    def update_value(self, value):
        if self._value == value:   # don't update if there is no change
            return
        self._value = value

        update_value_callback = self._updateValueCallback
        if update_value_callback:
            update_value_callback([value])

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

    def onWriteRequest(self, data, offset, withoutResponse, callback):
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG)
        # elif not (self._minLength <= len(data) <= self._maxLength):
        #     callback(Characteristic.RESULT_INVALID_ATTRIBUTE_LENGTH)
        elif self._callbackFn(data):
            callback(Characteristic.RESULT_SUCCESS)
        else:
            callback(Characteristic.RESULT_UNLIKELY_ERROR)


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
        # TODO Bad naming. Subscribe would suggest that we can do it multiple times.
        # However this is more like "setCallback"

        self._updateValueCallback = update_value_callback

    def onUnsubscribe(self):
        self._updateValueCallback = None

    def update(self, value):
        self._value = value

        callback = self._updateValueCallback
        if callback:
            callback(value)



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


class ProgramStatusCharacteristic(BrainToMobileFunctionCharacteristic):
    """ Store/send button script states to mobile. """
    def update_button_value(self, button_id: int, status: int):
        """ Handles low level packing. """
        if not self._value:
            state_array = [0]*32
        else:
            state_array = unpack_2_bit_number_array_32(self._value)

        state_array[button_id] = status

        log(f'button state array id:{button_id} => stat: {status}')

        packed_byte_array = pack_2_bit_number_array_32(state_array)

        # log(f'Button state change: {packed_byte_array}')
        # If there are multiple messages, here is where we want to throttle.
        self.update(packed_byte_array)



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

    def __init__(self, uuid, version_info):
        super().__init__({
            'uuid':       uuid,
            'properties': ['read'],
            'value':      version_info.encode()
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
    def __init__(self, system_id):
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
            callback(Characteristic.RESULT_SUCCESS, self._system_id.encode('utf-8'))

    def onWriteRequest(self, data, offset, withoutResponse, callback):
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

    def onWriteRequest(self, data, offset, withoutResponse, callback):
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

    def onWriteRequest(self, data, offset, withoutResponse, callback):
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

class UnifiedBatteryInfoCharacteristic(CustomBatteryLevelCharacteristic):
    def onReadRequest(self, offset, callback):
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG, None)
        else:
            callback(Characteristic.RESULT_SUCCESS, self._value)

    def update_value(self, battery_status: BatteryStatus):

        new_value = [
            round(battery_status.main),
            battery_status.chargerStatus,
            round(battery_status.motor),
            battery_status.motor_battery_present
        ]
        if new_value == self._value:
            return

        self._value = new_value

        if self._updateValueCallback:
            self._updateValueCallback(self._value)

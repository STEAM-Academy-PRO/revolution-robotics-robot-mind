""" Define Bluetooth communication protocols """

from enum import Enum
import struct
import traceback
from typing import Generic, TypeVar

from pybleno import Characteristic, Descriptor
from revvy.bluetooth.data_types import (
    GyroData,
    ProgramStatusCollection,
    ScriptVariables,
    TimerData,
)
from revvy.bluetooth.longmessage import (
    LongMessageError,
    LongMessageHandler,
    LongMessageProtocol,
    LongMessageProtocolResult,
)
from revvy.robot.robot import BatteryStatus

from revvy.utils.logger import get_logger
from revvy.utils.serialize import Serialize

log = get_logger("BLE Characteristics")


class ValidateState(Enum):
    UNKNOWN = 0
    IN_PROGRESS = 1
    DONE = 2


class ValidateConfigCharacteristic(Characteristic):
    def __init__(self, uuid, description: bytes, callback) -> None:
        self._on_write_callback = callback
        self._value = struct.pack("<I", 0)
        self.state = ValidateState.UNKNOWN
        super().__init__(
            {
                "uuid": uuid,
                "properties": ["write", "read"],
                "descriptors": [
                    Descriptor({"uuid": "2901", "value": description}),
                ],
            }
        )

    def onWriteRequest(self, data, offset, withoutResponse, callback) -> None:
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG)
        elif len(data) != 7:
            log("validate_config::onWriteRequest::wrong length")
            callback(Characteristic.RESULT_INVALID_ATTRIBUTE_LENGTH)
        elif self._on_write_callback(data):
            callback(Characteristic.RESULT_SUCCESS)
        else:
            callback(Characteristic.RESULT_UNLIKELY_ERROR)

    def onReadRequest(self, offset, callback) -> None:
        log("validate_config::onReadRequest")
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG, None)
        else:
            callback(Characteristic.RESULT_SUCCESS, self._value)

    def updateValue(self, state: ValidateState, motors_bitmask, sensors) -> None:
        self.state = state
        self._value = struct.pack(
            "BBBBBB", state.value, motors_bitmask, sensors[0], sensors[1], sensors[2], sensors[3]
        )

        log(f"validate_config::update: {self._value}")


class BackgroundProgramControlCharacteristic(Characteristic):
    def __init__(self, uuid, description: bytes, callback) -> None:
        self._value = []
        self._callbackFn = callback
        super().__init__(
            {
                "uuid": uuid,
                "properties": ["read", "notify", "write"],
                "descriptors": [
                    Descriptor({"uuid": "2901", "value": description}),
                ],
            }
        )

    def onReadRequest(self, offset, callback) -> None:
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG, None)
        else:
            callback(Characteristic.RESULT_SUCCESS, self._value)

    def updateValue(self, value) -> None:
        self._value = value

        update_notified_value = self.updateValueCallback
        if update_notified_value:
            update_notified_value(self._value)

    def onWriteRequest(self, data, offset, withoutResponse, callback) -> None:
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG)
        # elif not (self._minLength <= len(data) <= self._maxLength):
        #     callback(Characteristic.RESULT_INVALID_ATTRIBUTE_LENGTH)
        elif self._callbackFn(data):
            callback(Characteristic.RESULT_SUCCESS)
        else:
            callback(Characteristic.RESULT_UNLIKELY_ERROR)


# DataType = TypeVar('DataType', bound=Serialize)
DataType = TypeVar("DataType", bound=Serialize)


class BrainToMobileCharacteristic(Characteristic, Generic[DataType]):
    def __init__(self, uuid, description: bytes) -> None:
        self._value = bytes()
        super().__init__(
            {
                "uuid": uuid,
                "properties": ["read", "notify"],
                "descriptors": [
                    Descriptor({"uuid": "2901", "value": description}),
                ],
            }
        )

    def resetValue(self) -> None:
        self._update_value(bytes())

    def onReadRequest(self, offset, callback) -> None:
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG, None)
        else:
            callback(Characteristic.RESULT_SUCCESS, self._value)

    def updateValue(self, value: DataType) -> None:
        if isinstance(value, Serialize):
            value = value.__bytes__()
        self._update_value(value)

    def _update_value(self, value: bytes) -> None:
        self._value = value

        update_notified_value = self.updateValueCallback
        if update_notified_value:
            update_notified_value(self._value)


class StateControlCharacteristic(BackgroundProgramControlCharacteristic):
    pass


class SensorCharacteristic(BrainToMobileCharacteristic):
    def updateValue(self, value: Serialize) -> None:
        valueBytes = value.__bytes__()
        # FIXME: prefix with data length is probably unnecessary
        super().updateValue(bytes([len(valueBytes), *valueBytes]))


class GyroCharacteristic(BrainToMobileCharacteristic[GyroData]):
    pass


class TimerCharacteristic(BrainToMobileCharacteristic[TimerData]):
    pass


class ReadVariableCharacteristic(BrainToMobileCharacteristic[ScriptVariables]):
    pass


class ProgramStatusCharacteristic(BrainToMobileCharacteristic[ProgramStatusCollection]):
    """Store/send button script states to mobile."""

    def __init__(self, uuid, description: bytes) -> None:
        super().__init__(uuid, description)
        self._data = ProgramStatusCollection()

    def resetValue(self) -> None:
        self._data = ProgramStatusCollection()
        self.updateValue(self._data)

    def updateButtonStatus(self, button_id: int, status: int) -> None:
        self._data.update_button_value(button_id, status)
        self.updateValue(self._data)


# Device Information Service
class ReadOnlyCharacteristic(Characteristic):
    def __init__(self, uuid, value) -> None:
        super().__init__({"uuid": uuid, "properties": ["read"], "value": value})


class MobileToBrainFunctionCharacteristic(Characteristic):
    def __init__(self, uuid, min_length, max_length, description: bytes, callback) -> None:
        self._callbackFn = callback
        self._minLength = min_length
        self._maxLength = max_length
        self._value = struct.pack("<I", 0)
        super().__init__(
            {
                "uuid": uuid,
                "properties": ["write", "read", "notify"],
                "descriptors": [
                    Descriptor({"uuid": "2901", "value": description}),
                ],
            }
        )

    def onWriteRequest(self, data, offset, withoutResponse, callback) -> None:
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG)
        elif not (self._minLength <= len(data) <= self._maxLength):
            callback(Characteristic.RESULT_INVALID_ATTRIBUTE_LENGTH)
        elif self._callbackFn(data):
            callback(Characteristic.RESULT_SUCCESS)
        else:
            callback(Characteristic.RESULT_UNLIKELY_ERROR)

    def onReadRequest(self, offset, callback) -> None:
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG, None)
        else:
            callback(Characteristic.RESULT_SUCCESS, self._value)

    def updateValue(self, value) -> None:
        self._value = value

        update_notified_value = self.updateValueCallback
        if update_notified_value:
            update_notified_value(self._value)


class LongMessageCharacteristic(Characteristic):
    def __init__(self, handler: LongMessageHandler):
        super().__init__(
            {
                "uuid": "d59bb321-7218-4fb9-abac-2f6814f31a4d",
                "properties": ["read", "write"],
            }
        )
        self._handler = LongMessageProtocol(handler)

    def onReadRequest(self, offset, callback) -> None:
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG)
        else:
            try:
                value = self._handler.handle_read()
                callback(Characteristic.RESULT_SUCCESS, value)

            except LongMessageError:
                callback(Characteristic.RESULT_UNLIKELY_ERROR, None)

    @staticmethod
    def _translate_result(result: LongMessageProtocolResult) -> int:
        if result == LongMessageProtocolResult.RESULT_SUCCESS:
            return Characteristic.RESULT_SUCCESS
        elif result == LongMessageProtocolResult.RESULT_INVALID_ATTRIBUTE_LENGTH:
            return Characteristic.RESULT_INVALID_ATTRIBUTE_LENGTH
        else:
            return Characteristic.RESULT_UNLIKELY_ERROR

    def onWriteRequest(self, data, offset, withoutResponse, callback) -> None:
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

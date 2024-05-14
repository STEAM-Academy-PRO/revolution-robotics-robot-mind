""" Device communication related services """

from revvy.bluetooth.ble_characteristics import ReadOnlyCharacteristic
from revvy.bluetooth.services.ble import BleService
from revvy.utils.functions import get_serial
from revvy.utils.version import VERSION
from pybleno import Characteristic
from revvy.utils.device_name import get_device_name, set_device_name


# These are standard BLE characteristics, so we don't set a custom descriptor string for them
class SerialNumberCharacteristic(ReadOnlyCharacteristic):
    def __init__(self, serial: str) -> None:
        super().__init__("2A25", serial.encode())


class ManufacturerNameCharacteristic(ReadOnlyCharacteristic):
    def __init__(self, name: bytes) -> None:
        super().__init__("2A29", name)


class ModelNumberCharacteristic(ReadOnlyCharacteristic):
    def __init__(self, model_no: bytes) -> None:
        super().__init__("2A24", model_no)


class VersionCharacteristic(Characteristic):
    version_max_length = 20

    # FIXME
    def __init__(self, uuid, version_info) -> None:
        super().__init__({"uuid": uuid, "properties": ["read"], "value": version_info.encode()})
        self._version = []

    def onReadRequest(self, offset, callback) -> None:
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG, None)
        else:
            callback(Characteristic.RESULT_SUCCESS, self._version)

    def updateValue(self, version) -> None:
        if len(version) > self.version_max_length:
            version = version[: self.version_max_length]
        self._version = version.encode("utf-8")


class SystemIdCharacteristic(Characteristic):
    def __init__(self) -> None:
        super().__init__({"uuid": "2A23", "properties": ["read", "write"]})

    def onReadRequest(self, offset, callback) -> None:
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG, None)
        else:
            callback(Characteristic.RESULT_SUCCESS, get_device_name().encode("utf-8"))

    def onWriteRequest(self, data: bytes, offset, withoutResponse, callback) -> None:
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG)
        else:
            try:
                name = data.decode("ascii")
                if 0 < len(name) <= 15:
                    set_device_name(name)
                    callback(Characteristic.RESULT_SUCCESS)
                else:
                    callback(Characteristic.RESULT_UNLIKELY_ERROR)
            except UnicodeDecodeError:
                callback(Characteristic.RESULT_UNLIKELY_ERROR)


class DeviceInformationService(BleService):
    """Channel to send system info via Bluetooth"""

    def __init__(self) -> None:
        super().__init__(
            "180A",
            {
                "hw_version": VersionCharacteristic(uuid="2A27", version_info=str(VERSION.hw)),
                "fw_version": VersionCharacteristic(uuid="2A26", version_info=str(VERSION.fw)),
                "sw_version": VersionCharacteristic(uuid="2A28", version_info=str(VERSION.sw)),
                "serial_number": SerialNumberCharacteristic(get_serial()),
                "manufacturer_name": ManufacturerNameCharacteristic(b"RevolutionRobotics"),
                "model_number": ModelNumberCharacteristic(b"RevvyAlpha"),
                "system_id": SystemIdCharacteristic(),
            },
        )

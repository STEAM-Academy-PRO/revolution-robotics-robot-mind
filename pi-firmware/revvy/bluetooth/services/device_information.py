""" Device communication related services """

from revvy.bluetooth.ble_characteristics import ManufacturerNameCharacteristic
from revvy.bluetooth.ble_characteristics import ModelNumberCharacteristic
from revvy.bluetooth.ble_characteristics import SerialNumberCharacteristic
from revvy.bluetooth.ble_characteristics import SystemIdCharacteristic, VersionCharacteristic

from revvy.bluetooth.services.ble import BleService
from revvy.utils.functions import get_serial
from revvy.utils.version import VERSION


class DeviceInformationService(BleService):
    """Channel to send system info via Bluetooth"""

    def __init__(self):
        hw = VersionCharacteristic(uuid="2A27", version_info=str(VERSION.hw))
        fw = VersionCharacteristic(uuid="2A26", version_info=str(VERSION.fw))
        sw = VersionCharacteristic(uuid="2A28", version_info=str(VERSION.sw))
        serial = SerialNumberCharacteristic(get_serial())
        manufacturer_name = ManufacturerNameCharacteristic(b"RevolutionRobotics")
        model_number = ModelNumberCharacteristic(b"RevvyAlpha")
        system_id = SystemIdCharacteristic()

        super().__init__(
            "180A",
            {
                "hw_version": hw,
                "fw_version": fw,
                "sw_version": sw,
                "serial_number": serial,
                "manufacturer_name": manufacturer_name,
                "model_number": model_number,
                "system_id": system_id,
            },
        )

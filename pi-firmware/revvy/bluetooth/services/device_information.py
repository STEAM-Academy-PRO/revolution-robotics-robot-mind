""" Device communication related services """

from revvy.bluetooth.ble_characteristics import ManufacturerNameCharacteristic, ModelNumberCharacteristic, SerialNumberCharacteristic, SystemIdCharacteristic, VersionCharacteristic
from revvy.bluetooth.services.ble import BleService

from revvy.utils.observable import Observable

class DeviceInformationService(BleService):
    """ Channel to send system info via Bluetooth """
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

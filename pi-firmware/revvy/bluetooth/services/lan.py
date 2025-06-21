import socket
from revvy.bluetooth.services.ble import BleService
from pybleno import Characteristic, Descriptor

def get_local_ip():
    # Try to determine the local IP address by connecting to a public address (does not send packets)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # The IP doesn't need to be reachable; no packets are sent
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return '0.0.0.0'

class LanInfoCharacteristic(Characteristic):
    def __init__(self, uuid, description):
        super().__init__(
            {
                "uuid": uuid,
                "properties": ["read"],
                "descriptors": [Descriptor({"uuid": "2901", "value": description})],
            }
        )
        self._value = get_local_ip().encode('utf-8')
        print(f"LAN Info Characteristic initialized with IP: {self._value.decode('utf-8')}")

    def onReadRequest(self, offset, callback) -> None:
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG, None)
        else:
            callback(
                Characteristic.RESULT_SUCCESS,
                self._value,
            )
    def updateValue(self) -> None:
        new_value = get_local_ip().encode('utf-8')
        if new_value == self._value:
            return

        self._value = new_value

        update_notified_value = self.updateValueCallback
        if update_notified_value:
            update_notified_value(self._value)

class LanAddressService(BleService):
    def __init__(self):
        print("Initializing LAN Address Service")
        super().__init__(
            "12345678-1234-5678-1234-56789abcdef0",
            {
                "lan_info": LanInfoCharacteristic("12345678-1234-5678-1234-56789abcdef1", b"LAN Info"),
            },
        )
        self._lan_info_characteristic = self.characteristic("lan_info")
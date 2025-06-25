import socket
from pybleno import BlenoPrimaryService
from pybleno import Characteristic, Descriptor
from revvy.bluetooth.services.ble import BleService

# from revvy.bluetooth.ble_characteristics import BrainToMobileCharacteristic

from revvy.utils.logger import get_logger

log = get_logger("WLAN")

def get_local_ip():
    # Try to determine the local IP address by connecting to a public address (does not send packets)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # The IP doesn't need to be reachable; no packets are sent
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return '0.0.0.0'

class LanIpCharacteristic(Characteristic):
    def __init__(self, uuid, description):
        super().__init__(
            {
                "uuid": uuid,
                "properties": ["read"],
                "descriptors": [Descriptor({"uuid": "2901", "value": description})],
            }
        )
        self._value = get_local_ip().encode('utf-8')
        log(f"LAN Info Characteristic initialized with IP: {self._value.decode('utf-8')}")

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


class WlanCredentialsCharacteristic(Characteristic):
    def __init__(self, uuid, description):
        log("Initializing WLAN Credentials Characteristic")
        super().__init__(
            {
                "uuid": uuid,
                "properties": ["read", "write"],
                "descriptors": [Descriptor({"uuid": "2901", "value": description})],
            }
        )
        self._value = b""

    def onReadRequest(self, offset, callback) -> None:
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG, None)
        else:
            callback(
                Characteristic.RESULT_SUCCESS,
                self._value,
            )
    def onWriteRequest(self, data: bytes, offset, withoutResponse, callback) -> None:
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG)
        else:
            try:
                self._value = data
                print(f"WLAN SSID Characteristic updated: {self._value.decode('utf-8')}")
                callback(Characteristic.RESULT_SUCCESS)
            except UnicodeDecodeError:
                callback(Characteristic.RESULT_UNLIKELY_ERROR)


class NetworkStatusCharacteristic(Characteristic):
    def __init__(self, uuid, description):
        super().__init__(
            {
                "uuid": uuid,
                "properties": ["read", "notify"],
                "descriptors": [Descriptor({"uuid": "2901", "value": description})],
            }
        )
        self._value = b"Disconnected"

    def onReadRequest(self, offset, callback) -> None:
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG, None)
        else:
            callback(
                Characteristic.RESULT_SUCCESS,
                self._value,
            )

    def updateValue(self, status: str) -> None:
        new_value = status.encode('utf-8')
        if new_value == self._value:
            return

        self._value = new_value

        update_notified_value = self.updateValueCallback
        if update_notified_value:
            update_notified_value(self._value)

    def setStatus(self, status: str) -> None:
        print(f"Setting network status to: {status}")
        self.updateValue(status)



class LanAddressService(BleService):
    def __init__(self):
        log("Initializing LAN Address Service")

        self._lan_ip_characteristic = LanIpCharacteristic("12345678-1234-5678-1234-56789abcdef2", b"LAN Info")
        # self._wlan_credentials_characteristic = WlanCredentialsCharacteristic("12345678-1234-5678-1234-56789abcdef3", b"WLAN Credentials")
        # self._network_status_characteristic = NetworkStatusCharacteristic("12345678-1234-5678-1234-56789abcdef4", b"Network Status")

        super().__init__(
            "12345678-1234-5678-1234-56789abcdef0",
            {
                "lan_info": self._lan_ip_characteristic,
                # "wlan_credentials": self._wlan_credentials_characteristic,
                # "network_status": self._network_status_characteristic,
            },
        )
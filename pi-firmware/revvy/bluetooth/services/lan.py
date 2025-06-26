import socket
import stat
import subprocess
from time import sleep
from pybleno import BlenoPrimaryService
from pybleno import Characteristic, Descriptor
from revvy.bluetooth.services.ble import BleService

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

def update_wifi_settings(ssid, password, statusCallback = lambda x: None):
    try:
        # Write credentials to wpa_supplicant.conf
        wpa_conf = '/home/pi/network_config/wpa_supplicant.conf'

        statusCallback(f"Updating WiFi settings for SSID: {ssid}")
        new_config = f'''
        ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
        update_config=1
        country=US

        network={{
            ssid="{ssid}"
            psk="{password}"
        }}
        '''

        statusCallback(f"Updating WiFi settings for SSID: {ssid}")

        # Backup old config
        # try:
        #     subprocess.run(['cp', wpa_conf, wpa_conf + '.bak'], check=True)
        # except subprocess.CalledProcessError as e:
        #     log(f"Failed to backup wpa_supplicant.conf: {e}")

        # # Write new config
        # statusCallback('Deleting old wpa_supplicant.conf...')
        # try:
        #     subprocess.run(['rm', '-f', wpa_conf], check=True)
        # except subprocess.CalledProcessError as e:
        #     log(f"Failed to delete old wpa_supplicant.conf: {e}")

        statusCallback('Writing new wpa_supplicant.conf...')
        with open(wpa_conf, 'w') as f:
            f.write(new_config)

        # Reload wpa_supplicant
        statusCallback("Reloading wpa_supplicant with new credentials...")
        subprocess.run(['sudo', 'wpa_cli', '-i', 'wlan0', 'reconfigure'], check=True)
        # Optionally, bring interface down and up
        statusCallback("Restarting wlan0 interface...")
        subprocess.run(['sudo', 'ifdown', 'wlan0'], check=False)
        statusCallback("Bringing wlan0 back up...")
        subprocess.run(['sudo', 'ifup', 'wlan0'], check=False)

        # Check interface status
        statusCallback("Checking wlan0 interface status...")
        try:
            result = subprocess.run(['/usr/sbin/iwconfig', 'wlan0'], capture_output=True, text=True, check=True)
            output = result.stdout
            if "ESSID:off/any" in output or "Not-Associated" in output:
                statusCallback("Failed to connect: Interface not associated with any network.")
                return False, "Failed to connect: Interface not associated with any network."
            elif "Access Point: Not-Associated" in output:
                statusCallback("Failed to connect: No access point found.")
                return False, "Failed to connect: No access point found."
            elif "Encryption key:off" in output:
                statusCallback("Failed to connect: Encryption key is off.")
                return False, "Failed to connect: Encryption key is off."
            elif "Invalid" in output or "failed" in output.lower():
                statusCallback("Failed to connect: Invalid credentials or connection failure.")
                return False, "Failed to connect: Invalid credentials or connection failure."
            elif "ESSID" in output and ssid in output:
                statusCallback(f"Successfully connected to {ssid}.")
            else:
                statusCallback("Connection status unclear, please check manually.")
                return True, f"Successfully connected to {ssid}."
        except subprocess.CalledProcessError as e:
            statusCallback(f"Failed to get interface status: {e}")
            return False, f"Failed to get interface status: {e}"
    except Exception as e:
        statusCallback(f"Error updating WiFi settings: {e}")
        return False, f"Failed to update WiFi: {e}"



class LanIpCharacteristic(Characteristic):
    def __init__(self, uuid, description):
        super().__init__(
            {
                "uuid": uuid,
                "properties": ["read", "notify"],
                "descriptors": [Descriptor({"uuid": "2901", "value": description})],
            }
        )
        self._value = get_local_ip().encode('utf-8')
        log(f"LAN Info Characteristic initialized with IP: {self._value.decode('utf-8')}")

    def onReadRequest(self, offset, callback) -> None:
        self._value = get_local_ip().encode('utf-8')
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
        log(f"Status:: {status}")
        self.updateValue(status)



class WlanCredentialsCharacteristic(Characteristic):
    def __init__(self, uuid, description, network_status_characteristic: NetworkStatusCharacteristic):
        log("Initializing WLAN Credentials Characteristic")
        super().__init__(
            {
                "uuid": uuid,
                "properties": ["read", "write"],
                "descriptors": [Descriptor({"uuid": "2901", "value": description})],
            }
        )
        self._value = b""
        self._network_status_characteristic = network_status_characteristic

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
                ssid = self._value.decode('utf-8').split('\0')[0]
                password = self._value.decode('utf-8').split('\0')[1] if '\0' in self._value.decode('utf-8') else ''
                log(f"WLAN Credentials Received - SSID: {ssid}, Password: {password}")
                callback(Characteristic.RESULT_SUCCESS)
                if (self._network_status_characteristic is not None):
                    log("Updating network status characteristic with WLAN credentials")
                    self._network_status_characteristic.setStatus("Wifi Credentials Received for " + ssid)
                update_wifi_settings(ssid, password, statusCallback=self._network_status_characteristic.updateValue)
                sleep(5)
                ip = get_local_ip()
                self._network_status_characteristic.setStatus(f"Connected to {ssid} with IP {ip}")


            except UnicodeDecodeError:
                callback(Characteristic.RESULT_UNLIKELY_ERROR)



class LanAddressService(BleService):
    def __init__(self):
        log("Initializing LAN Address Service")

        self._lan_ip_characteristic = LanIpCharacteristic("12345678-1234-5678-1234-56789abcdef2", b"LAN Info")
        self._network_status_characteristic = NetworkStatusCharacteristic("12345678-1234-5678-1234-56789abcdef5", b"Network Status")
        self._wlan_credentials_characteristic = WlanCredentialsCharacteristic("12345678-1234-5678-1234-56789abcdef3", b"WLAN Credentials", self._network_status_characteristic) # self._network_status_characteristic)

        super().__init__(
            "12345678-1234-5678-1234-56789abcdef0",
            {
                "lan_info": self._lan_ip_characteristic,
                "wlan_credentials": self._wlan_credentials_characteristic,
                "network_status": self._network_status_characteristic,
            },
        )
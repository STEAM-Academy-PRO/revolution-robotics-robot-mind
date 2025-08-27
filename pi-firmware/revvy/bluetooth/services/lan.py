import socket
import threading
import subprocess
from time import sleep
from pybleno import BlenoPrimaryService
from pybleno import Characteristic, Descriptor
from revvy.bluetooth.services.ble import BleService

from revvy.utils.logger import get_logger
import fcntl
import struct

IFACE = 'wlan0'

log = get_logger("WLAN")

def watch_ip_changes(callback):
    """
    Watch for changes in the IP address of the specified interface.
    Calls the callback every 3 seconds with the current IP, if valid
    """

    def watcher():
        last_ip = ''
        while True:
            ip = get_local_ip()
            if ip != "0.0.0.0":
                if last_ip != ip:
                    log(f"IP address changed: {last_ip} -> {ip}")
                    last_ip = ip
                callback(ip)
            else:
                log("No valid IP address found, retrying...")

            sleep(3)

    t = threading.Thread(target=watcher, daemon=True)
    t.start()
    return watcher

def get_local_ip():
    # Get the IP address assigned to wlan0 interface only

    try:
        iface = IFACE.encode('utf-8')
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ip = fcntl.ioctl(
            s.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack('256s', iface[:15])
        )[20:24]
        return socket.inet_ntoa(ip)
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
        statusCallback('Writing new wpa_supplicant.conf...')
        try:
            with open(wpa_conf, 'w') as f:
                f.write(new_config)
        except PermissionError as e:
            log(f"Permission denied while writing wpa_supplicant.conf: {e}")
            statusCallback(f"Permission denied: {e}")
            return False, f"Permission denied: {e}"
        except Exception as e:
            log(f"Error writing wpa_supplicant.conf: {e}")
            statusCallback(f"Error writing wpa_supplicant.conf: {e}")
            return False, f"Error writing wpa_supplicant.conf: {e}"

        # Reload wpa_supplicant
        statusCallback("Reloading wpa_supplicant with new credentials...")
        try:
            subprocess.run(['sudo', 'wpa_cli', '-i', 'wlan0', 'reconfigure'], check=True)
        except subprocess.CalledProcessError as e:
            log(f"Failed to reload wpa_supplicant: {e}")
            statusCallback(f"Failed to reload wpa_supplicant: {e}")
            return False, f"Failed to reload wpa_supplicant: {e}"

        statusCallback("Bringing wlan0 down...")
        try:
            subprocess.run(['sudo', 'ip', 'link', 'set', 'wlan0', 'down'], check=True)
        except subprocess.CalledProcessError as e:
            log(f"Failed to bring wlan0 down: {e}")
            statusCallback(f"Failed to bring wlan0 down: {e}")
            return False, f"Failed to bring wlan0 down: {e}"

        statusCallback("Bringing wlan0 up...")
        try:
            subprocess.run(['sudo', 'ip', 'link', 'set', 'wlan0', 'up'], check=True)
        except subprocess.CalledProcessError as e:
            log(f"Failed to bring wlan0 up: {e}")
            statusCallback(f"Failed to bring wlan0 up: {e}")
            return False, f"Failed to bring wlan0 up: {e}"

        # Check interface status
        statusCallback("Checking wlan0 interface status...")
        try:
            result = subprocess.run(['/usr/sbin/iwconfig', 'wlan0'], capture_output=True, text=True, check=True)
            output = result.stdout
            if "ESSID:off/any" in output or "Not-Associated" in output:
                statusCallback("Failed to connect: Interface not associated with any network.")
                log("Failed to connect: Interface not associated with any network.")
                return False, "Failed to connect: Interface not associated with any network."
            elif "Access Point: Not-Associated" in output:
                statusCallback("Failed to connect: No access point found.")
                log("Failed to connect: No access point found.")
                return False, "Failed to connect: No access point found."
            elif "Encryption key:off" in output:
                statusCallback("Failed to connect: Encryption key is off.")
                log("Failed to connect: Encryption key is off.")
                return False, "Failed to connect: Encryption key is off."
            elif "Invalid" in output or "failed" in output.lower():
                statusCallback("Failed to connect: Invalid credentials or connection failure.")
                log("Failed to connect: Invalid credentials or connection failure.")
                return False, "Failed to connect: Invalid credentials or connection failure."
            elif "ESSID" in output and ssid in output:
                statusCallback(f"Successfully connected to {ssid}.")
                log(f"Successfully connected to {ssid}.")
            else:
                statusCallback("Connection status unclear, please check manually.")
                log("Connection status unclear, please check manually.")
                return True, f"Successfully connected to {ssid}."
        except subprocess.CalledProcessError as e:
            statusCallback(f"Failed to get interface status: {e}")
            log(f"Failed to get interface status: {e}")
            return False, f"Failed to get interface status: {e}"
    except Exception as e:
        statusCallback(f"Error updating WiFi settings: {e}")
        log(f"Error updating WiFi settings: {e}")
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

    def onReadRequest(self, offset, callback) -> None:
        self._value = get_local_ip().encode('utf-8')
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG, None)
        else:
            callback(
                Characteristic.RESULT_SUCCESS,
                self._value,
            )
    def updateValue(self, new_value) -> None:
        new_value = new_value or get_local_ip()
        if new_value == self._value:
            return

        self._value = new_value

        update_notified_value = self.updateValueCallback
        if update_notified_value:
            update_notified_value(self._value.encode('utf-8'))



class NetworkStatusCharacteristic(Characteristic):
    def __init__(self, uuid, description):
        super().__init__(
            {
                "uuid": uuid,
                "properties": ["read", "notify"],
                "descriptors": [Descriptor({"uuid": "2901", "value": description})],
            }
        )
        self._value = b"Initializing..."

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

        # self._value = new_value

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

                self._network_status_characteristic.setStatus(f"Connecting to {ssid}, waiting for IP")

            except UnicodeDecodeError:
                callback(Characteristic.RESULT_UNLIKELY_ERROR)


class LanAddressService(BleService):
    def __init__(self):
        log("Initializing LAN Address Service")

        self._lan_ip_characteristic = LanIpCharacteristic("12345678-1234-5678-1234-56789abcdef2", b"LAN Info")
        self._network_status_characteristic = NetworkStatusCharacteristic("12345678-1234-5678-1234-56789abcdef5", b"Network Status")
        self._wlan_credentials_characteristic = WlanCredentialsCharacteristic("12345678-1234-5678-1234-56789abcdef3", b"WLAN Credentials", self._network_status_characteristic) # self._network_status_characteristic)

        def send_ip_status(addrs):
            # log(f"Ip associated: {addrs} - notifying ble")
            self._lan_ip_characteristic.updateValue(addrs)

        # Start watching for IP changes and update the characteristic, let the user know if the wifi address changes.
        watch_ip_changes(send_ip_status)

        super().__init__(
            "12345678-1234-5678-1234-56789abcdef0",
            {
                "lan_info": self._lan_ip_characteristic,
                "wlan_credentials": self._wlan_credentials_characteristic,
                "network_status": self._network_status_characteristic,
            },
        )
import array
from typing import Callable, Optional
from . import UuidUtil
from .hci_socket import *
from .hci_socket.Emit import Emit


class Error(Exception):
    def __init__(self, message: str):
        self.message = message

    def call_or_raise(self, callback: Optional[Callable[["Error"], None]]):
        if callback:
            callback(self)
        else:
            raise self


class Bleno(Emit):
    def __init__(self) -> None:
        super().__init__()

        self.platform = "unknown"
        self.state = "unknown"
        self.address = "unknown"
        self.rssi = 0
        self.mtu = 20

        self._bindings = BlenoBindings()

        self._bindings.on("stateChange", self.onStateChange)
        self._bindings.on("platform", self.onPlatform)
        self._bindings.on("addressChange", self.onAddressChange)
        self._bindings.on("advertisingStart", self.onAdvertisingStart)
        self._bindings.on("advertisingStop", self.onAdvertisingStop)
        self._bindings.on("servicesSet", self.onServicesSet)
        self._bindings.on("accept", self.onAccept)
        self._bindings.on("mtuChange", self.onMtuChange)
        self._bindings.on("disconnect", self.onDisconnect)

        self._bindings.on("rssiUpdate", self.onRssiUpdate)

    def start(self) -> None:
        self._bindings.init()

    def onPlatform(self, platform) -> None:
        self.platform = platform

    def onStateChange(self, state) -> None:
        self.state = state

        self.emit("stateChange", [state])

    def onAddressChange(self, address) -> None:
        # debug('addressChange ' + address);

        self.address = address

    def onAccept(self, clientAddress) -> None:
        # debug('accept ' + clientAddress);
        self.emit("accept", [clientAddress])

    def onMtuChange(self, mtu) -> None:
        # debug('mtu ' + mtu);

        self.mtu = mtu

        self.emit("mtuChange", [mtu])

    def onDisconnect(self, clientAddress) -> None:
        # debug('disconnect ' + clientAddress);
        self.emit("disconnect", [clientAddress])

    def startAdvertising(
        self, name, service_uuids=None, callback: Optional[Callable] = None
    ) -> None:
        if self.state != "poweredOn":
            error = Error(f"Could not start advertising, state is {self.state} (not poweredOn)")
            error.call_or_raise(callback)

        else:
            if callback:
                self.once("advertisingStart", [], callback)

        if service_uuids is None:
            service_uuids = []
        undashedServiceUuids = list(map(UuidUtil.removeDashes, service_uuids))

        # print 'starting advertising %s %s' % (name, undashedServiceUuids)
        self._bindings.startAdvertising(name, undashedServiceUuids)

    def startAdvertisingIBeacon(
        self,
        uuid,
        major,
        minor,
        measuredPower,
        callback: Optional[Callable[["Error"], None]] = None,
    ) -> None:
        if self.state != "poweredOn":
            error = Error(f"Could not start advertising, state is {self.state} (not poweredOn)")
            error.call_or_raise(callback)

        else:
            undashedUuid = UuidUtil.removeDashes(uuid)
            uuidData = bytearray.fromhex(undashedUuid)
            uuidDataLength = len(uuidData)
            iBeaconData = array.array("B", [0] * (uuidDataLength + 5))

            for i in range(0, uuidDataLength):
                iBeaconData[i] = uuidData[i]

            writeUInt16BE(iBeaconData, major, uuidDataLength)
            writeUInt16BE(iBeaconData, minor, uuidDataLength + 2)
            writeInt8(iBeaconData, measuredPower, uuidDataLength + 4)

            if callback:
                self.once("advertisingStart", [], callback)

            # debug('iBeacon data = ' + iBeaconData.toString('hex'));

            self._bindings.startAdvertisingIBeacon(iBeaconData)

    def startAdvertisingWithEIRData(
        self, advertisementData, scanData, callback: Optional[Callable[["Error"], None]] = None
    ) -> None:
        # if (typeof scanData === 'function')
        if hasattr(scanData, "__call__") is True:
            callback = scanData
            scanData = None

        if self.state != "poweredOn":
            error = Error(f"Could not start advertising, state is {self.state} (not poweredOn)")
            error.call_or_raise(callback)

        else:
            if callback:
                self.once("advertisingStart", [], callback)

        # print 'starting advertising with EIR data %s %s' % (advertisementData, scanData)
        self._bindings.startAdvertisingWithEIRData(advertisementData, scanData)

    def onAdvertisingStart(self, error) -> None:
        # debug('advertisingStart: ' + error);
        if error:
            self.emit("advertisingStartError", [error])
        else:
            self.emit("advertisingStart", [error])

    def stopAdvertising(self, callback=None) -> None:
        if callback:
            self.once("advertisingStop", [], callback)

        self._bindings.stopAdvertising()

    def onAdvertisingStop(self) -> None:
        # debug('advertisingStop');
        self.emit("advertisingStop", [])

    def setServices(self, services, callback=None) -> None:
        if callback:
            self.once("servicesSet", [], callback)
        # print 'setting services %s' % services
        self._bindings.setServices(services)

    def onServicesSet(self, error=None) -> None:
        # debug('servicesSet');

        if error:
            self.emit("servicesSetError", [error])

        self.emit("servicesSet", [error])

    def disconnect(self) -> None:
        # debug('disconnect');
        self._bindings.disconnect()

    def updateRssi(self, callback=None) -> None:
        if callback:
            self.once("rssiUpdate", [], callback)

        self._bindings.updateRssi()

    def onRssiUpdate(self, rssi) -> None:
        self.emit("rssiUpdate", [rssi])

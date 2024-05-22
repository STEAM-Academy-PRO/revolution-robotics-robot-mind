import platform
from typing import Optional
from .Emit import Emit

from .Hci import Hci
from .Gap import Gap
from .Gatt import Gatt
from .AclStream import AclStream


class BlenoBindings(Emit):
    def __init__(self) -> None:
        super().__init__()
        self._state = None

        self._advertising = False

        self._hci = Hci()
        self._gap = Gap(self._hci)
        self._gatt = Gatt()  # self._hci)

        self._address = None
        self._handle = None
        self._aclStream: Optional[AclStream] = None

    def startAdvertising(self, name, serviceUuids) -> None:
        self._advertising = True

        self._gap.startAdvertising(name, serviceUuids)

    def startAdvertisingIBeacon(self, data) -> None:
        self._advertising = True

        self._gap.startAdvertisingIBeacon(data)

    def startAdvertisingWithEIRData(self, advertisementData, scanData) -> None:
        self._advertising = True

        self._gap.startAdvertisingWithEIRData(advertisementData, scanData)

    def stopAdvertising(self) -> None:
        self._advertising = False

        self._gap.stopAdvertising()

    def setServices(self, services) -> None:
        self._gatt.setServices(services)

        self.emit("servicesSet", [])

    def disconnect(self) -> None:
        if self._handle:
            # debug('disconnect by server')

            self._hci.disconnect(self._handle)

    def updateRssi(self) -> None:
        if self._handle:
            self._hci.readRssi(self._handle)

    def init(self) -> None:
        # self.onSigIntBinded = this.onSigInt

        # process.on('SIGINT', self.onSigIntBinded)
        # process.on('exit', self.onExit)

        self._gap.on("advertisingStart", self.onAdvertisingStart)
        self._gap.on("advertisingStop", self.onAdvertisingStop)

        self._gatt.on("mtuChange", self.onMtuChange)

        self._hci.on("stateChange", self.onStateChange)
        self._hci.on("addressChange", self.onAddressChange)
        self._hci.on("readLocalVersion", self.onReadLocalVersion)

        self._hci.on("leConnComplete", self.onLeConnComplete)
        self._hci.on("leConnUpdateComplete", self.onLeConnUpdateComplete)
        self._hci.on("rssiRead", self.onRssiRead)
        self._hci.on("disconnComplete", self.onDisconnComplete)
        self._hci.on("encryptChange", self.onEncryptChange)
        self._hci.on("leLtkNegReply", self.onLeLtkNegReply)
        self._hci.on("aclDataPkt", self.onAclDataPkt)

        self.emit("platform", [platform.system()])

        self._hci.init()

    def onStateChange(self, state) -> None:
        if self._state == state:
            return

        self._state = state

        if state == "unauthorized":
            print("Bleno warning: adapter state unauthorized, please run as root or with sudo")
            print("               or see README for information on running without root/sudo:")
            print("               https://github.com/sandeepmistry/bleno#running-on-linux")
        elif state == "unsupported":
            print(
                "Bleno warning: adapter does not support Bluetooth Low Energy (BLE, Bluetooth Smart)."
            )
            print("               Try to run with environment variable:")
            print("               [sudo] BLENO_HCI_DEVICE_ID=x node ...")

        self.emit("stateChange", [state])

    def onAddressChange(self, address) -> None:
        self.emit("addressChange", [address])

    def onReadLocalVersion(self, hciVer, hciRev, lmpVer, manufacturer, lmpSubVer) -> None:
        pass

    def onAdvertisingStart(self, error) -> None:
        self.emit("advertisingStart", [error])

    def onAdvertisingStop(self) -> None:
        self.emit("advertisingStop", [])

    def onLeConnComplete(
        self,
        status,
        handle,
        role,
        addressType,
        address,
        interval,
        latency,
        supervisionTimeout,
        masterClockAccuracy,
    ) -> None:
        if role != 1:
            # not slave, ignore
            return

        self._address = address
        self._handle = handle
        self._aclStream = AclStream(
            self._hci, handle, self._hci.addressType, self._hci.address, addressType, address
        )
        self._gatt.setAclStream(self._aclStream)

        self.emit("accept", [address])

    def onLeConnUpdateComplete(self, status, handle, interval, latency, supervisionTimeout) -> None:
        # no-op
        pass

    def onDisconnComplete(self, handle, reason) -> None:
        if self._aclStream:
            self._aclStream.push(None, None)

        address = self._address

        self._address = None
        self._handle = None
        self._aclStream = None

        if address:
            self.emit("disconnect", [address])  # TODO: use reason

        if self._advertising:
            self._gap.restartAdvertising()

    def onEncryptChange(self, handle, encrypt) -> None:
        if self._handle == handle and self._aclStream:
            self._aclStream.pushEncrypt(encrypt)

    def onLeLtkNegReply(self, handle) -> None:
        if self._handle == handle and self._aclStream:
            self._aclStream.pushLtkNegReply()

    def onMtuChange(self, mtu) -> None:
        self.emit("mtuChange", [mtu])

    def onRssiRead(self, handle, rssi) -> None:
        self.emit("rssiUpdate", [rssi])

    def onAclDataPkt(self, handle, cid, data) -> None:
        if self._handle == handle and self._aclStream:
            self._aclStream.push(cid, data)

from .emit import Emit
from revvy.bluetooth.pybleno.hci_socket import Hci
from .Smp import Smp


class AclStream(Emit):
    def __init__(
        self, hci: Hci, handle, localAddressType, localAddress, remoteAddressType, remoteAddress
    ) -> None:
        super().__init__()
        self._hci = hci
        self._handle = handle
        self.encrypted = False

        self._smp = Smp(self, localAddressType, localAddress, remoteAddressType, remoteAddress)

    def write(self, cid, data) -> None:
        self._hci.queueAclDataPkt(self._handle, cid, data)

    def push(self, cid, data) -> None:
        if data:
            self.emit("data", [cid, data])
        else:
            self.emit("end", [])

    def pushEncrypt(self, encrypt) -> None:
        self.encrypted = True if encrypt else False

        self.emit("encryptChange", [self.encrypted])

    def pushLtkNegReply(self) -> None:
        self.emit("ltkNegReply", [])

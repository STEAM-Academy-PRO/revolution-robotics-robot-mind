from Emit import Emit
from .Smp import Smp


class AclStream(Emit):
    def __init__(
        self, hci, handle, localAddressType, localAddress, remoteAddressType, remoteAddress
    ):
        super().__init__()
        self._hci = hci
        self._handle = handle
        self.encrypted = False

        self._smp = Smp(self, localAddressType, localAddress, remoteAddressType, remoteAddress)

    def write(self, cid, data):
        self._hci.writeAclDataPkt(self._handle, cid, data)

    def push(self, cid, data):
        if data:
            self.emit("data", [cid, data])
        else:
            self.emit("end", [])

    def pushEncrypt(self, encrypt):
        self.encrypted = True if encrypt else False

        self.emit("encryptChange", [self.encrypted])

    def pushLtkNegReply(self):
        self.emit("ltkNegReply", [])

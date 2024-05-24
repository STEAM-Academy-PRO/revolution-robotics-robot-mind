import math
import time
from .Emit import Emit
from .BluetoothHCI import *

from .constants2 import *
from .Io import *
from .HciStatus import *


class Hci(Emit):
    def __init__(self) -> None:
        super().__init__()

        self._socket = BluetoothHCI(auto_start=False)
        self._isDevUp = None
        self._state = None
        self._deviceId = None
        # le-u min payload size + l2cap header size
        # see Bluetooth spec 4.2 [Vol 3, Part A, Chapter 4]
        self._aclMtu = 23 + 4
        self._aclMaxInProgress = 1

        self.resetBuffers()

        self.on("stateChange", self.onStateChange)

    def init(self) -> None:

        self._socket.on_data(self.onSocketData)

        self._socket.on_started(self.on_socket_started)

        # self._socket_up_poll_thread = threading.Thread(target=self._socket_up_poller, name='HCISocketUpPoller')
        # self._socket_up_poll_thread.setDaemon(True)
        # self._socket_up_poll_thread.start()

        self._socket.start()

    #     self._socket_up_poll_thread = threading.Thread(target=self.io_thread, name='HCISocketUpPoller2')
    #     self._socket_up_poll_thread.setDaemon(True)
    #     self._socket_up_poll_thread.start()

    # def io_thread(self):
    #     while True:

    #         pass

    def initDev(self) -> None:
        self.setEventMask()
        self.setLeEventMask()
        self.readLocalVersion()
        self.writeLeHostSupported()
        self.readLeHostSupported()
        self.readBdAddr()
        self.leReadBufferSize()

    def resetBuffers(self) -> None:
        self._mainHandle = None
        self._handleAclsInProgress: dict[int, int] = {}
        self._handleBuffers = {}
        self._aclOutQueue = []

    def setSocketFilter(self) -> None:
        typeMask = (1 << HCI_EVENT_PKT) | (1 << HCI_ACLDATA_PKT)
        eventMask1 = (
            (1 << EVT_DISCONN_COMPLETE)
            | (1 << EVT_ENCRYPT_CHANGE)
            | (1 << EVT_CMD_COMPLETE)
            | (1 << EVT_CMD_STATUS)
            | (1 << EVT_NUMBER_OF_COMPLETED_PACKETS)
        )
        eventMask2 = 1 << (EVT_LE_META_EVENT - 32)
        opcode = 0

        # debug('setting filter to: ' + filter.toString('hex'))
        filter = struct.pack("<LLLH", typeMask, eventMask1, eventMask2, opcode)
        self._socket.set_filter(filter)

    def setEventMask(self) -> None:
        # cmd = new Buffer(12)
        # eventMask = new Buffer('fffffbff07f8bf3d', 'hex')

        ## header
        # cmd.writeUInt8(HCI_COMMAND_PKT, 0)
        # cmd.writeUInt16LE(SET_EVENT_MASK_CMD, 1)

        ## length
        # cmd.writeUInt8(eventMask.length, 3)

        # eventMask.copy(cmd, 4)

        cmd = array.array("B", [0] * 12)
        struct.pack_into("<BHB", cmd, 0, HCI_COMMAND_PKT, SET_EVENT_MASK_CMD, 8)
        struct.pack_into(">Q", cmd, 4, 0xFFFFFBFF07F8BF3D)
        # debug('set event mask - writing: ' + cmd.toString('hex'))
        self.write(cmd)

    def reset(self) -> None:
        cmd = array.array("B", [0] * 4)

        # header
        writeUInt8(cmd, HCI_COMMAND_PKT, 0)
        writeUInt16LE(cmd, OCF_RESET | OGF_HOST_CTL << 10, 1)

        # length
        writeUInt8(cmd, 0x00, 3)

        # debug('reset');
        self.write(cmd)

    def readLeHostSupported(self) -> None:
        cmd = array.array("B", [0] * 4)

        # header
        writeUInt8(cmd, HCI_COMMAND_PKT, 0)
        writeUInt16LE(cmd, READ_LE_HOST_SUPPORTED_CMD, 1)

        # length
        writeUInt8(cmd, 0x00, 3)
        # struct.pack_into("<BHB", cmd, 0, HCI_COMMAND_PKT, READ_LE_HOST_SUPPORTED_CMD, 0x00)

        # debug('read LE host supported - writing: ' + cmd.toString('hex'))
        self.write(cmd)

    def writeLeHostSupported(self) -> None:
        # cmd = new Buffer(6)
        cmd = array.array("B", [0] * 6)

        # header
        writeUInt8(cmd, HCI_COMMAND_PKT, 0)
        writeUInt16LE(cmd, WRITE_LE_HOST_SUPPORTED_CMD, 1)

        # length
        writeUInt8(cmd, 0x02, 3)

        # data
        writeUInt8(cmd, 0x01, 4)  # le
        writeUInt8(cmd, 0x00, 5)  # simul

        # struct.pack_into("<BHBBB", cmd, 0, HCI_COMMAND_PKT, WRITE_LE_HOST_SUPPORTED_CMD, 0x02, 0x01, 0x00)

        # debug('write LE host supported - writing: ' + cmd.toString('hex'))
        # print [hex(c) for c in cmd]
        self.write(cmd)

    def readLocalVersion(self) -> None:
        cmd = array.array("B", [0] * 4)

        # header
        writeUInt8(cmd, HCI_COMMAND_PKT, 0)
        writeUInt16LE(cmd, READ_LOCAL_VERSION_CMD, 1)

        # length
        writeUInt8(cmd, 0x0, 3)
        # struct.pack_into("<BHB", cmd, 0, HCI_COMMAND_PKT, READ_LOCAL_VERSION_CMD, 0)

        # debug('read local version - writing: ' + cmd.toString('hex'))
        self.write(cmd)

    def readBdAddr(self) -> None:
        cmd = array.array("B", [0] * 4)
        # header
        writeUInt8(cmd, HCI_COMMAND_PKT, 0)
        writeUInt16LE(cmd, READ_BD_ADDR_CMD, 1)

        # length
        writeUInt8(cmd, 0x0, 3)
        # struct.pack_into("<BHB", cmd, 0, HCI_COMMAND_PKT, READ_BD_ADDR_CMD, 0x00)

        # debug('read bd addr - writing: ' + cmd.toString('hex'))
        self.write(cmd)

    def setLeEventMask(self) -> None:
        # #cmd = new Buffer(12)
        # cmd = array.array('B', [0] * 12)
        # #leEventMask = new Buffer('1f00000000000000', 'hex')
        # leEventMask = '1f00000000000000'

        # # # header
        # # cmd.writeUInt8(HCI_COMMAND_PKT, 0)
        # # cmd.writeUInt16LE(LE_SET_EVENT_MASK_CMD, 1)
        # struct.pack_into("<BH", cmd, 0, HCI_COMMAND_PKT, LE_SET_EVENT_MASK_CMD)

        # # # length
        # #cmd.writeUInt8(leEventMask.length, 3)
        # struct.pack_into("<B", cmd, 3, len(leEventMask) / 2)

        # struct.pack_into(">Q", cmd, 4, int(leEventMask, 16))
        # #leEventMask.copy(cmd, 4)

        # #debug('set le event mask - writing: ' + cmd.toString('hex'))
        # #print [hex(c) for c in cmd]
        # self.write(cmd)
        cmd = array.array("B", [0] * 12)
        leEventMask = array.array("B", bytearray.fromhex("1f00000000000000"))

        # header
        writeUInt8(cmd, HCI_COMMAND_PKT, 0)
        writeUInt16LE(cmd, LE_SET_EVENT_MASK_CMD, 1)

        # length
        writeUInt8(cmd, len(leEventMask), 3)

        copy(leEventMask, cmd, 4)

        # debug('set le event mask - writing: ' + cmd.toString('hex'));
        # console.log('set le event mask - writing: ' + cmd.toString('hex'));
        self.write(cmd)

    def setAdvertisingParameters(self) -> None:
        # cmd = new Buffer(19)
        cmd = array.array("B", [0] * 19)

        # # header
        # cmd.writeUInt8(HCI_COMMAND_PKT, 0)
        # cmd.writeUInt16LE(LE_SET_ADVERTISING_PARAMETERS_CMD, 1)

        # # length
        # cmd.writeUInt8(15, 3)

        # advertisementInterval = Math.floor((process.env.BLENO_ADVERTISING_INTERVAL ? parseFloat(process.env.BLENO_ADVERTISING_INTERVAL) : 100) * 1.6)
        advertisementInterval = math.floor(100 * 1.6)

        # # data
        # cmd.writeUInt16LE(advertisementInterval, 4); # min interval
        # cmd.writeUInt16LE(advertisementInterval, 6); # max interval
        # cmd.writeUInt8(0x00, 8); # adv type
        # cmd.writeUInt8(0x00, 9); # own addr typ
        # cmd.writeUInt8(0x00, 10); # direct addr type
        # (new Buffer('000000000000', 'hex')).copy(cmd, 11); # direct addr
        # cmd.writeUInt8(0x07, 17)
        # cmd.writeUInt8(0x00, 18)

        struct.pack_into(
            "<BHBHHBBBIHBB",
            cmd,
            0,
            HCI_COMMAND_PKT,
            LE_SET_ADVERTISING_PARAMETERS_CMD,
            15,
            advertisementInterval,
            advertisementInterval,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x07,
            0x00,
        )

        # debug('set advertisement parameters - writing: ' + cmd.toString('hex'))
        # print('set advertise parameters - writing: ' + `[hex(c) for c in cmd]`)
        self.write(cmd)

    def setAdvertisingData(self, data) -> None:
        cmd = array.array("B", [0] * 36)

        # cmd.fill(0x00)

        # header
        writeUInt8(cmd, HCI_COMMAND_PKT, 0)
        writeUInt16LE(cmd, LE_SET_ADVERTISING_DATA_CMD, 1)

        # length
        writeUInt8(cmd, 32, 3)

        # data
        writeUInt8(cmd, len(data), 4)
        copy(data, cmd, 5)

        # debug('set advertisement data - writing: ' + cmd.toString('hex'))
        self.write(cmd)

    def setScanResponseData(self, data) -> None:
        cmd = array.array("B", [0] * 36)
        #     cmd.fill(0x00)

        # header
        writeUInt8(cmd, HCI_COMMAND_PKT, 0)
        writeUInt16LE(cmd, LE_SET_SCAN_RESPONSE_DATA_CMD, 1)

        # length
        writeUInt8(cmd, 32, 3)

        # data
        writeUInt8(cmd, len(data), 4)
        copy(data, cmd, 5)

        # debug('set scan response data - writing: ' + cmd.toString('hex'))
        # print('set scan response data - writing: ' + `[hex(c) for c in cmd]`)
        self.write(cmd)

    def setAdvertiseEnable(self, enabled) -> None:
        cmd = array.array("B", [0] * 5)

        # header
        writeUInt8(cmd, HCI_COMMAND_PKT, 0)
        writeUInt16LE(cmd, LE_SET_ADVERTISE_ENABLE_CMD, 1)

        # length
        writeUInt8(cmd, 0x01, 3)

        # data
        writeUInt8(cmd, 0x01 if enabled else 0x00, 4)  # enable: 0 -> disabled, 1 -> enabled
        # struct.pack_into("<BHBB", cmd, 0, HCI_COMMAND_PKT, LE_SET_ADVERTISE_ENABLE_CMD, 0x01, 0x01 if enabled else 0x00 )

        # debug('set advertise enable - writing: ' + cmd.toString('hex'))
        self.write(cmd)

    def disconnect(self, handle, reason=None) -> None:
        cmd = array.array("B", [0] * 7)

        reason = reason or HCI_OE_USER_ENDED_CONNECTION

        # header
        writeUInt8(cmd, HCI_COMMAND_PKT, 0)
        writeUInt16LE(cmd, DISCONNECT_CMD, 1)

        # length
        writeUInt8(cmd, 0x03, 3)

        # data
        writeUInt16LE(cmd, handle, 4)  # handle
        writeUInt8(cmd, reason, 6)  # reason

        # debug('disconnect - writing: ' + cmd.toString('hex'))
        self.write(cmd)

    def readRssi(self, handle) -> None:
        cmd = array.array("B", [0] * 6)

        # header
        writeUInt8(cmd, HCI_COMMAND_PKT, 0)
        writeUInt16LE(cmd, READ_RSSI_CMD, 1)

        # length
        writeUInt8(cmd, 0x02, 3)

        # data
        writeUInt16LE(cmd, handle, 4)  # handle

        # debug('read rssi - writing: ' + cmd.toString('hex'))
        self.write(cmd)

    def leReadBufferSize(self) -> None:
        pkt = array.array("B", [0] * 4)

        # header
        writeUInt8(pkt, HCI_COMMAND_PKT, 0)
        writeUInt16LE(pkt, LE_READ_BUFFER_SIZE_CMD, 1)
        writeUInt8(pkt, 0x0, 3)  # data length 0

        # debug('le read buffer size - writing: ' + pkt.toString('hex'))
        self.write(pkt)

    def readBufferSize(self) -> None:
        pkt = array.array("B", [0] * 4)

        # header
        writeUInt8(pkt, HCI_COMMAND_PKT, 0)
        writeUInt16LE(pkt, READ_BUFFER_SIZE_CMD, 1)
        writeUInt8(pkt, 0x0, 3)  # data length 0

        # debug('read buffer size - writing: ' + pkt.toString('hex'))
        self.write(pkt)

    def queueAclDataPkt(self, handle, cid, data) -> None:
        hf = handle | ACL_START_NO_FLUSH << 12
        l2capPdu = array.array("B", [0] * (4 + len(data)))

        # header
        writeUInt16LE(l2capPdu, len(data), 0)
        writeUInt16LE(l2capPdu, cid, 2)
        copy(data, l2capPdu, 4)
        fragId = 0

        while len(l2capPdu) > 0:
            frag = l2capPdu[0 : self._aclMtu]
            l2capPdu = l2capPdu[self._aclMtu :]

            # hci header
            pkt = array.array("B", [0] * (5 + len(frag)))
            writeUInt8(pkt, HCI_ACLDATA_PKT, 0)
            writeUInt16LE(pkt, hf, 1)
            hf |= ACL_CONT << 12
            writeUInt16LE(pkt, len(frag), 3)
            copy(frag, pkt, 5)

            self._aclOutQueue.append({"handle": handle, "pkt": pkt, "fragId": fragId})

            fragId += 1

        self.pushAclOutQueue()

    def pushAclOutQueue(self) -> None:
        inProgress = 0
        for count in self._handleAclsInProgress.values():
            inProgress += count

        while inProgress < self._aclMaxInProgress and len(self._aclOutQueue):
            inProgress = inProgress + 1
            self.writeOneAclDataPkt()

        # if (inProgress >= self._aclMaxInProgress and self._aclOutQueue.length):
        # printf("acl out queue congested")
        # printf("\tin progress = {inProgress}")
        # printf("\twaiting = {self._aclOutQueue.length}")

    def writeOneAclDataPkt(self) -> None:
        pkt = self._aclOutQueue.pop(0)
        if pkt["handle"] not in self._handleAclsInProgress:
            # handle is closed, do not throw exception
            # FIXME: this is a hack, Gatt notifications should be properly cleared instead
            return

        self._handleAclsInProgress[pkt["handle"]] += 1
        # debug(
        #     "write acl data pkt frag "
        #     + pkt.fragId
        #     + " handle "
        #     + pkt.handle
        #     + " - writing: "
        #     + pkt.pkt.toString("hex")
        # )
        self._socket.write(pkt["pkt"])

    def write(self, pkt) -> None:
        # print 'WRITING: %s' % ''.join(format(x, '02x') for x in pkt)
        self._socket.write(pkt)

    def onSocketData(self, data) -> None:
        # print 'READING: %s' % ''.join(format(x, '02x') for x in data)
        # print 'got data!'
        # print [hex(c) for c in data]
        # s = struct.Struct('B')
        # unpacked_data = s.unpack(data)
        # print char.from_bytes(data)

        # eventType = data.readUInt8(0)
        # handle
        eventType = data[0]

        # debug('\tevent type = ' + eventType)
        # print('\tevent type = ' + `eventType`)

        if HCI_EVENT_PKT == eventType:
            subEventType = readUInt8(data, 1)

            # debug('\tsub event type = ' + subEventType)
            # print('\t\tsub event type = ' + `subEventType`)

            if subEventType == EVT_DISCONN_COMPLETE:
                handle = readUInt16LE(data, 4)

                if handle != self._mainHandle:
                    return

                reason = readUInt8(data, 6)

                # debug('\t\thandle = ' + handle)
                # debug('\t\treason = ' + reason)
                # print('\t\thandle = ' + `handle`)
                # print('\t\treason = ' + `reason`)

                # As per Bluetooth Core specs:
                # When the Host receives a Disconnection Complete, Disconnection Physical
                # Link Complete or Disconnection Logical Link Complete event, the Host shall
                # assume that all unacknowledged HCI Data Packets that have been sent to the
                # Controller for the returned Handle have been flushed, and that the
                # corresponding data buffers have been freed.
                del self._handleAclsInProgress[handle]
                self._mainHandle = None
                aclOutQueue = []
                discarded = 0
                for pkt in self._aclOutQueue:
                    if pkt["handle"] != handle:
                        aclOutQueue.append(pkt)
                    else:
                        discarded += 1

                # if discarded:
                #     debug('\t\tacls discarded = ' + discarded);

                self._aclOutQueue = aclOutQueue
                self.pushAclOutQueue()

                self.emit("disconnComplete", [handle, reason])

            elif subEventType == EVT_ENCRYPT_CHANGE:
                handle = readUInt16LE(data, 4)
                encrypt = readUInt8(data, 6)

                # debug('\t\thandle = ' + handle)
                # debug('\t\tencrypt = ' + encrypt)
                self.emit("encryptChange", [handle, encrypt])
            elif subEventType == EVT_CMD_COMPLETE:
                # ncmd = readUInt8(data, 3)
                cmd = readUInt16LE(data, 4)
                status = readUInt8(data, 6)
                result = data[7:]

                # debug('\t\tncmd = ' + ncmd);
                # debug('\t\tcmd = ' + cmd)
                # debug('\t\tstatus = ' + status)
                # debug('\t\tresult = ' + result.toString('hex'))
                # print('\t\tcmd = ' + `cmd`)
                # print('\t\tstatus = ' + `status`)
                # print('\t\tresult = ' + `result`);

                self.processCmdCompleteEvent(cmd, status, result)
            elif subEventType == EVT_LE_META_EVENT:
                leMetaEventType = readUInt8(data, 3)
                leMetaEventStatus = readUInt8(data, 4)
                leMetaEventData = data[5:]

                # debug('\t\tLE meta event type = ' + leMetaEventType)
                # debug('\t\tLE meta event status = ' + leMetaEventStatus)
                # debug('\t\tLE meta event data = ' + leMetaEventData.toString('hex'))

                self.processLeMetaEvent(leMetaEventType, leMetaEventStatus, leMetaEventData)

            elif subEventType == EVT_NUMBER_OF_COMPLETED_PACKETS:
                handles = readUInt8(data, 3)
                for pkt in range(handles):
                    handle = readUInt16LE(data, 4 + pkt * 4)
                    pkts = readUInt16LE(data, 6 + pkt * 4)
                    # debug("\thandle = " + handle);
                    # debug("\t\tcompleted = " + pkts);
                    if handle not in self._handleAclsInProgress:
                        # debug("\t\talready closed")
                        continue

                    if pkts > self._handleAclsInProgress[handle]:
                        # Linux kernel may send acl packets by itself, so be ready for underflow
                        self._handleAclsInProgress[handle] = 0
                    else:
                        self._handleAclsInProgress[handle] -= pkts

                    # debug("\t\tin progress = " + self._handleAclsInProgress[handle]);

                self.pushAclOutQueue()

        elif HCI_ACLDATA_PKT == eventType:
            flags = readUInt16LE(data, 1) >> 12
            handle = readUInt16LE(data, 1) & 0x0FFF

            if ACL_START == flags:
                cid = readUInt16LE(data, 7)

                length = readUInt16LE(data, 5)
                pktData = data[9:]

                # debug('\t\tcid = ' + cid)

                if length == len(pktData):
                    # debug('\t\thandle = ' + handle)
                    # debug('\t\tdata = ' + pktData.toString('hex'))

                    self.emit("aclDataPkt", [handle, cid, pktData])
                else:
                    self._handleBuffers[handle] = {"length": length, "cid": cid, "data": pktData}
            elif ACL_CONT == flags:
                if not handle in self._handleBuffers or not "data" in self._handleBuffers[handle]:
                    return
                self._handleBuffers[handle]["data"] = self._handleBuffers[handle]["data"] + data[5:]

                if (
                    len(self._handleBuffers[handle]["data"])
                    == self._handleBuffers[handle]["length"]
                ):
                    self.emit(
                        "aclDataPkt",
                        [
                            handle,
                            self._handleBuffers[handle]["cid"],
                            self._handleBuffers[handle]["data"],
                        ],
                    )

                    del self._handleBuffers[handle]

        # print 'READ: %s' % ''.join(format(x, '02x') for x in data)

    def onSocketError(self, error) -> None:
        # debug('onSocketError: ' + error.message);
        if error.message == "Operation not permitted":
            self.emit("stateChange", ["unauthorized"])
        elif error.message == "Network is down":
            pass  # no-op

    def processCmdCompleteEvent(self, cmd, status, result) -> None:
        # handle
        if cmd == RESET_CMD:
            self.initDev()
        elif cmd == READ_LE_HOST_SUPPORTED_CMD:
            if status == 0:
                le = readUInt8(result, 0)
                simul = readUInt8(result, 1)

            #     debug('\t\t\tle = ' + le)
            #     debug('\t\t\tsimul = ' + simul)
        elif cmd == READ_LOCAL_VERSION_CMD:
            hciVer = readUInt8(result, 0)
            hciRev = readUInt16LE(result, 1)
            lmpVer = readInt8(result, 3)
            manufacturer = readUInt16LE(result, 4)
            lmpSubVer = readUInt16LE(result, 6)

            if hciVer < 0x06:
                self.emit("stateChange", "unsupported")
            elif self._state != "poweredOn":
                self.setAdvertiseEnable(False)
                self.setAdvertisingParameters()

            self.emit("readLocalVersion", [hciVer, hciRev, lmpVer, manufacturer, lmpSubVer])

        elif cmd == READ_BD_ADDR_CMD:
            self.addressType = "public"
            # self.address = hex(result).match(/.{1,2}/g).reverse().join(':')
            self.address = "%02x:%02x:%02x:%02x:%02x:%02x" % struct.unpack("BBBBBB", result)
            # debug('address = ' + this.address)

            self.emit("addressChange", [self.address])
        elif cmd == LE_SET_ADVERTISING_PARAMETERS_CMD:
            self.emit("stateChange", ["poweredOn"])

            self.emit("leAdvertisingParametersSet", [status])
        elif cmd == LE_SET_ADVERTISING_DATA_CMD:
            self.emit("leAdvertisingDataSet", [status])
        elif cmd == LE_SET_SCAN_RESPONSE_DATA_CMD:
            self.emit("leScanResponseDataSet", [status])
        elif cmd == LE_SET_ADVERTISE_ENABLE_CMD:
            self.emit("leAdvertiseEnableSet", [status])
        elif cmd == READ_RSSI_CMD:
            handle = readUInt16LE(result, 0)
            rssi = readInt8(result, 2)

            # debug('\t\t\thandle = ' + handle)
            # debug('\t\t\trssi = ' + rssi)
            # print('\t\t\thandle = ' + `handle`)
            # print('\t\t\trssi = ' + `rssi`);

            self.emit("rssiRead", [handle, rssi])
        elif cmd == LE_LTK_NEG_REPLY_CMD:
            handle = readUInt16LE(result, 0)

            # debug('\t\t\thandle = ' + handle)
            self.emit("leLtkNegReply", [handle])
        elif cmd == LE_READ_BUFFER_SIZE_CMD:
            if not status:
                self.processLeReadBufferSize(result)
        elif cmd == READ_BUFFER_SIZE_CMD:
            if not status:
                aclMtu = readUInt16LE(result, 0)
                aclMaxInProgress = readUInt16LE(result, 3)
                # sanity
                if aclMtu and aclMaxInProgress:
                    # debug('br/edr acl mtu = ' + aclMtu)
                    # debug('br/edr acl max pkts = ' + aclMaxInProgress)
                    self._aclMtu = aclMtu
                    self._aclMaxInProgress = aclMaxInProgress

    def processLeReadBufferSize(self, result) -> None:
        aclMtu = readUInt16LE(result, 0)
        aclMaxInProgress = readUInt8(result, 2)
        if not aclMtu:
            # as per Bluetooth specs
            # print("falling back to br/edr buffer size")
            self.readBufferSize()
        else:
            # print(f"le acl_mtu = {acl_mtu}")
            # print(f"le acl_queue = {acl_queue}")
            self._aclMtu = aclMtu
            self._aclMaxInProgress = aclMaxInProgress

    def processLeMetaEvent(self, eventType, status, data) -> None:
        if eventType == EVT_LE_CONN_COMPLETE:
            self.processLeConnComplete(status, data)
        elif eventType == EVT_LE_CONN_UPDATE_COMPLETE:
            self.processLeConnUpdateComplete(status, data)

    def processLeConnComplete(self, status, data) -> None:
        handle = readUInt16LE(data, 0)
        role = readUInt8(data, 2)
        addressType = "random" if readUInt8(data, 3) == 0x01 else "public"
        mac_data: array.array = data[4:10]
        mac_data.reverse()
        address = "%02x:%02x:%02x:%02x:%02x:%02x" % struct.unpack("BBBBBB", mac_data)
        interval = readUInt16LE(data, 10) * 1.25
        latency = readUInt16LE(data, 12)  # TODO: multiplier?
        supervisionTimeout = readUInt16LE(data, 14) * 10
        masterClockAccuracy = readUInt8(data, 16)  # TODO: multiplier?

        # debug('\t\t\thandle = ' + handle)
        # debug('\t\t\trole = ' + role)
        # debug('\t\t\taddress type = ' + addressType)
        # debug('\t\t\taddress = ' + address)
        # debug('\t\t\tinterval = ' + interval)
        # debug('\t\t\tlatency = ' + latency)
        # debug('\t\t\tsupervision timeout = ' + supervisionTimeout)
        # debug('\t\t\tmaster clock accuracy = ' + masterClockAccuracy)

        self._mainHandle = handle
        self._handleAclsInProgress[handle] = 0

        self.emit(
            "leConnComplete",
            [
                status,
                handle,
                role,
                addressType,
                address,
                interval,
                latency,
                supervisionTimeout,
                masterClockAccuracy,
            ],
        )

    def processLeConnUpdateComplete(self, status, data) -> None:
        handle = readUInt16LE(data, 0)
        interval = readUInt16LE(data, 2) * 1.25
        latency = readUInt16LE(data, 4)  # TODO: multiplier?
        supervisionTimeout = readUInt16LE(data, 6) * 10

        # debug('\t\t\thandle = ' + handle)
        # debug('\t\t\tinterval = ' + interval)
        # debug('\t\t\tlatency = ' + latency)
        # debug('\t\t\tsupervision timeout = ' + supervisionTimeout)

        self.emit("leConnUpdateComplete", [status, handle, interval, latency, supervisionTimeout])

    def onStateChange(self, state) -> None:
        self._state = state

    def isDevUp(self) -> bool:
        # for line in iter(popen("hciconfig").readline, ''):
        #     if "UP RUNNING" in line:
        #         return True
        # return False
        return True

    def on_socket_started(self) -> None:
        isDevUp = self.isDevUp()
        if self._isDevUp != isDevUp:
            self._isDevUp = isDevUp
            if isDevUp:
                self.setSocketFilter()
                self.initDev()
            else:
                self.emit("stateChange", ["poweredOff"])

    def _socket_up_poller(self) -> None:
        while True:
            # print(self._socket.get_device_info())
            # self._socket.device_up()
            # print(popen("hciconfig").read())
            # print(popen("hciconfig").read())
            isDevUp = self.isDevUp()

            if self._isDevUp != isDevUp:
                pass
                # self._isDevUp = isDevUp
                # if isDevUp:
                #     self.setSocketFilter()
                #     self._socket.start()
                #     def do():

                #         self.setEventMask()
                #         self.setLeEventMask()
                #         self.readLocalVersion()
                #         self.writeLeHostSupported()
                #         self.readLeHostSupported()
                #         self.readBdAddr()
                #     # # self._socket.invoke(do)
                #     do()
                #     #self.emit('stateChange', ['poweredOn'])
                #     pass
                # else:
                #     self.emit('stateChange', ['poweredOff'])

            time.sleep(1)
        # setTimeout(this.pollIsDevUp.bind(this), 1000);

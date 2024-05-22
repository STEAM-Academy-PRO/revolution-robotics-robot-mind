#!/usr/bin/python

# Bluetooth HCI Python library  (Experimental)
#
# Pure Python and standard library based module for interacting with the Bluetooth HCI.
# There is no dependency on the PyBluez Python/Native libraries, bluetoothd service or D-Bus.

# This can be considered to be a Pythonisation of the NodeJS NoBLE/ BLENo by Sandeep Mistry.

# Author:  Wayne Keenan
# email:   wayne@thebubbleworks.com
# Twitter: https://twitter.com/wkeenan


# Acknowledgements:

# Significant information taken from https://github.com/sandeepmistry/node-bluetooth-hci-socket
# With help from https://github.com/colin-guyon/py-bluetooth-utils and the BlueZ Python library.

import array
import struct
import fcntl
import socket
import threading
from threading import Event
import select
import os
import sys

from .BluetoothSocket import BluetoothSocket

from .constants import *

OGF_HOST_CTL = 0x03
OCF_RESET = 0x0003

# -------------------------------------------------
# Socket HCI transport API

# This socket based to the Bluetooth HCI.

# Strong candidate for refactoring into factory pattern to support
# alternate transports (e.g. serial) and easier mocking for automated testing.


class BluetoothHCISocketProvider:

    def __init__(self, device_id=0) -> None:
        self.device_id = device_id
        self._keep_running = True
        self._socket_on_data_user_callback = None
        self._socket_on_started = None
        self._socket_poll_thread = None
        self._l2sockets = {}

        self._socket = BluetoothSocket(
            socket.AF_BLUETOOTH, socket.SOCK_RAW, socket.BTPROTO_HCI  # pyright: ignore
        )

        # self._socket = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_RAW, socket.BTPROTO_HCI)
        # self._socket = BluetoothUserSocket()
        # self._socket = bluetooth.bluez._gethcisock(0)

        self._socket.setblocking(False)
        self.__r, self.__w = os.pipe()
        self._r = os.fdopen(self.__r, "r")
        self._w = os.fdopen(self.__w, "w")

    def __del__(self) -> None:
        self._keep_running = False

    def open(self) -> None:

        # TODO: specify channel: HCI_CHANNEL_RAW, HCI_CHANNEL_USER, HCI_CHANNEL_CONTROL
        # https://www.spinics.net/lists/linux-bluetooth/msg37345.html
        # self._socket.bind((self.device_id,))

        HCI_CHANNEL_RAW = 0
        HCI_CHANNEL_USER = 1
        self._socket.bind_hci(self.device_id, HCI_CHANNEL_RAW)
        # self._socket2.bind_l2(0, "0B:D8:28:EB:27:B8", cid=ATT_CID, addr_type=1)
        # self._socket2.connect_l2(0, "0B:D8:28:EB:27:B8", cid=ATT_CID, addr_type=1)

        # self.reset()

        self._socket_poll_thread = threading.Thread(
            target=self._socket_poller, name="HCISocketPoller"
        )
        self._socket_poll_thread.setDaemon(True)
        self._socket_poll_thread.start()

    def kernel_disconnect_workarounds(self, data) -> None:
        # print 'PRE KERNEL WORKAROUND %d' % len(data)

        if len(data) == 22 and [elem for elem in data[0:5]] == [0x04, 0x3E, 0x13, 0x01, 0x00]:
            handle = data[5]
            # get address
            set = data[9:15]
            # get device info
            dev_info = self.get_device_info()
            raw_set = [c for c in set]
            raw_set.reverse()
            # addz = ''.join([hex(c) for c in set])
            # set.reverse()
            addz = "%02x:%02x:%02x:%02x:%02x:%02x" % struct.unpack(
                "BBBBBB", array.array("B", raw_set)
            )
            socket2 = BluetoothSocket(
                socket.AF_BLUETOOTH, socket.SOCK_SEQPACKET, socket.BTPROTO_L2CAP  # pyright: ignore
            )

            socket2.bind_l2(
                0, dev_info["addr"], cid=ATT_CID, addr_type=0
            )  # addr_type=dev_info['type'])

            self._l2sockets[handle] = socket2
            try:
                result = socket2.connect_l2(0, addz, cid=ATT_CID, addr_type=data[8] + 1)
            except:
                pass
        elif len(data) == 7 and [elem for elem in data[0:4]] == [0x04, 0x05, 0x04, 0x00]:
            handle = data[4]

            socket2 = self._l2sockets[handle] if handle in self._l2sockets else None
            if socket2:
                # print 'GOT A SOCKET!'
                socket2.close()
                del self._l2sockets[handle]

    def reset(self) -> None:
        cmd = array.array("B", [0] * 4)

        # // header
        # cmd.writeUInt8(HCI_COMMAND_PKT, 0);
        # cmd.writeUInt16LE(OCF_RESET | OGF_HOST_CTL << 10, 1);

        # // length
        # cmd.writeUInt8(0x00, 3);

        struct.pack_into("<BHB", cmd, 0, HCI_COMMAND_PKT, OCF_RESET | OGF_HOST_CTL << 10, 0x00)

        # debug('reset');
        self.write_buffer(cmd)

    def close(self) -> None:
        self._socket.close()

    def send_cmd(self, cmd, data) -> array.array:
        arr = array.array("B", data)
        self.send_cmd_value(cmd, arr)
        return arr

    def send_cmd_value(self, cmd, value):
        fcntl.ioctl(self._socket.fileno(), cmd, value)

    def write_buffer(self, data) -> None:
        self._socket.send(data)

    def set_filter(self, data) -> None:
        # flt = bluez.hci_filter_new()
        # bluez.hci_filter_all_events(flt)
        # bluez.hci_filter_set_ptype(flt, bluez.HCI_EVENT_PKT)
        self._socket.setsockopt(socket.SOL_HCI, socket.HCI_FILTER, data)  # pyright: ignore
        # self._socket.setsockopt(socket.SOL_HCI, socket.HCI_FILTER, data)

    def invoke(self, callback) -> None:
        event = Event()
        self._msg = (event, callback)
        self._w.write(" ")
        event.wait()

    def _socket_poller(self) -> None:
        if self._socket_on_started:
            self._socket_on_started()

        while self._keep_running:
            readable, writable, exceptional = select.select([self._socket, self._r], [], [])
            for s in readable:

                if s == self._r:
                    self._r.read(1)
                    assert self._msg
                    self._msg[1]()
                    self._msg[0].set()
                    self._msg = None
                elif s == self._socket:
                    data = self._socket.recv(1024)  # blocking
                    self.kernel_disconnect_workarounds(data)
                    if self._socket_on_data_user_callback:
                        self._socket_on_data_user_callback(bytearray(data))

    def on_started(self, callback) -> None:
        self._socket_on_started = callback

    def on_data(self, callback) -> None:
        self._socket_on_data_user_callback = callback

    def get_device_info(self) -> dict:

        # C hci_dev_info struct defined at https://git.kernel.org/pub/scm/bluetooth/bluez.git/tree/lib/hci.h#n2382
        hci_dev_info_struct = struct.Struct("=H 8s 6B L B 8B 3L 4I 10L")

        request_dta = hci_dev_info_struct.pack(
            self.device_id,
            b"",
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
        )

        response_data = self.send_cmd(HCIGETDEVINFO, request_dta)

        hci_dev_info = hci_dev_info_struct.unpack(response_data)

        # Just extract a few parts for now
        device_id = hci_dev_info[0]
        device_name = hci_dev_info[1].split(b"\0", 1)[0]
        bd_addr = "%0x:%0x:%0x:%0x:%0x:%0x" % hci_dev_info[7:1:-1]
        type = hci_dev_info[4]

        return dict(id=device_id, name=device_name, addr=bd_addr, type=type)


class BluetoothHCI:
    def __init__(self, device_id=0, auto_start: bool = True):
        # TODO: be given a provider interface from a factory (e.g. socket, serial, mock)
        self.hci = BluetoothHCISocketProvider(device_id)
        if auto_start:
            self.start()

    # -------------------------------------------------
    # Public HCI API, simply delegates to the composite HCI provider

    def start(self) -> None:
        self.hci.open()

    def stop(self) -> None:
        self.hci.close()

    def on_started(self, callback) -> None:
        self.hci.on_started(callback)

    def invoke(self, callback) -> None:
        self.hci.invoke(callback)

    def send_cmd(self, cmd, data) -> array.array:
        return self.hci.send_cmd(cmd, data)
        # packet type struct : https://git.kernel.org/pub/scm/bluetooth/bluez.git/tree/lib/hci.h#n117
        # typedef struct {
        #   uint16_t	opcode;		/* OCF & OGF */
        #   uint8_t		plen;
        #   } __attribute__ ((packed))	hci_command_hdr;
        # Op-code (16 bits): identifies the command:
        #    OGF (Op-code Group Field, most significant 6 bits);
        #    OCF (Op-code Command Field, least significant 10 bits)."""

    def send_cmd_value(self, cmd, value) -> None:
        self.hci.send_cmd_value(cmd, value)

    def write(self, data) -> None:
        self.hci.write_buffer(data)

    def set_filter(self, data) -> None:
        # self.device_down()
        self.hci.set_filter(data)
        # self.device_up()

    def on_data(self, callback) -> None:
        self.hci.on_data(callback)

    # -------------------------------------------------
    # Public HCI Convenience API

    def device_up(self) -> None:
        self.send_cmd_value(HCIDEVUP, self.hci.device_id)

    def device_down(self) -> None:
        self.send_cmd_value(HCIDEVDOWN, self.hci.device_id)

    def get_device_info(self) -> dict:
        return self.hci.get_device_info()

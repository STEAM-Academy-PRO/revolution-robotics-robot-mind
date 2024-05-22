# Copyright 2016 Mike Ryan
#
# This file is part of PyBT and is available under the MIT license. Refer to
# LICENSE for details.

from ctypes import CDLL, POINTER, Array, c_char, c_int, cdll, create_string_buffer, get_errno
import struct
import socket
import fcntl
import os
import array


from .BDAddr import *


class HCI_Channel:
    RAW = 0
    USER = 1
    MONITOR = 2
    CONTROL = 3
    LOGGING = 4


class _libc_adapter:
    def __init__(self) -> None:
        cdll.LoadLibrary("libc.so.6")
        libc = CDLL("libc.so.6", use_errno=True)

        bind = libc.bind
        bind.argtypes = (c_int, POINTER(c_char), c_int)
        bind.restype = c_int
        self.bind = bind

        connect = libc.connect
        connect.argtypes = (c_int, POINTER(c_char), c_int)
        connect.restype = c_int
        self.connect = connect

    def string(self, str) -> Array[c_char]:
        return create_string_buffer(str)


class BluetoothSocket(socket.socket):
    libc = _libc_adapter()

    def _sockaddr_l2(self, psm, bdaddr, cid, addr_type) -> bytes:
        return (
            struct.pack("<HH", socket.AF_BLUETOOTH, psm)
            + array.array("B", [ord(x) for x in BDAddr(bdaddr).le_string()])
            + struct.pack("<HH", cid, addr_type)
        )

    def _sockaddr_hci(self, dev, channel) -> bytes:
        if dev is None:
            dev = 0xFFFF
        return struct.pack("<HHH", socket.AF_BLUETOOTH, dev, channel)

    def _sockaddr_rc(self, bdaddr, channel) -> bytes:
        return (
            struct.pack("<H", socket.AF_BLUETOOTH)
            + array.array("B", [ord(x) for x in BDAddr(bdaddr).le_string()])
            + struct.pack("<H", channel)
        )

    def _sockaddr_sco(self, bdaddr) -> bytes:
        return struct.pack("<H", socket.AF_BLUETOOTH) + array.array(
            "B", [ord(x) for x in BDAddr(bdaddr).le_string()]
        )

    def _bind(self, sa) -> None:
        r = self.libc.bind(self.fileno(), self.libc.string(sa), len(sa))
        if r != 0:
            raise IOError(get_errno(), os.strerror(get_errno()))

    # bind to BTPROTO_L2CAP socket
    def bind_l2(self, psm, bdaddr, cid=0, addr_type=BDAddr.TYPE_BREDR) -> None:
        sa_str = self._sockaddr_l2(psm, bdaddr, cid, addr_type)
        self._bind(sa_str)

    # bind to BTPROTO_HCI socket
    def bind_hci(self, dev, channel) -> None:
        sa_str = self._sockaddr_hci(dev, channel)
        self._bind(sa_str)

    # bind to BTPROTO_RFCOMM socket
    def bind_rc(self, bdaddr, channel) -> None:
        sa_str = self._sockaddr_rc(bdaddr, channel)
        self._bind(sa_str)

    # bind to BTPROTO_SCO socket
    def bind_sco(self, bdaddr) -> None:
        sa_str = self._sockaddr_sco(bdaddr)
        self._bind(sa_str)

    def _connect(self, sa) -> None:
        r = self.libc.connect(self.fileno(), self.libc.string(sa), len(sa))
        if r != 0:
            raise IOError(get_errno(), os.strerror(get_errno()))

    # connect to BTPROTO_L2CAP socket
    def connect_l2(self, psm, bdaddr, cid=0, addr_type=BDAddr.TYPE_BREDR) -> None:
        sa_str = self._sockaddr_l2(psm, bdaddr, cid, addr_type)
        self._connect(sa_str)

    # connect to BTPROTO_HCI socket
    def connect_hci(self, dev, channel) -> None:
        sa_str = self._sockaddr_hci(dev, channel)
        self._connect(sa_str)

    # connect to BTPROTO_RFCOMM socket
    def connect_rc(self, bdaddr, channel) -> None:
        sa_str = self._sockaddr_rc(bdaddr, channel)
        self._connect(sa_str)

    # connect to BTPROTO_SCO socket
    def connect_sco(self, bdaddr) -> None:
        sa_str = self._sockaddr_sco(bdaddr)
        self._connect(sa_str)


def hci_devba(adapter=0) -> BDAddr:
    # Get Bluetooth device address
    # returns a BDAddr object
    dev_info = hci_devinfo(adapter)
    bd_addr = dev_info[10:16]
    return BDAddr(bd_addr)


def hci_devinfo(adapter=0) -> bytes:
    # Get Bluetooth device information
    # Takes an adapter number, returns raw data from ioctl
    # FIXME(MR) this function is a complete hack
    # but Python doesn't even dream of offering Bluetooth ioctl's
    dd = BluetoothSocket(
        socket.AF_BLUETOOTH, socket.SOCK_RAW, socket.BTPROTO_HCI  # pyright: ignore
    )
    dev_info = struct.pack("<H", adapter) + "\x00" * 90
    try:
        r = fcntl.ioctl(  # pyright: ignore
            dd, 0x800448D3, dev_info
        )  # HCIGETDEVINFO, tested on x64 Linux only
        return r
    except IOError as e:
        # XXX is there a more Pythonic way of doing this?
        if e[0] == 19:  # pyright: ignore
            raise TypeError("No such Bluetooth adapter")
        else:
            raise e

# SPDX-License-Identifier: GPL-3.0-only

from smbus2 import i2c_msg, SMBus
from revvy.mcu.rrrc_transport import RevvyTransportInterface, RevvyTransport, TransportException


class RevvyTransportI2CDevice(RevvyTransportInterface):
    """Low level communication class used to read/write a specific I2C device address"""
    def __init__(self, address, bus):
        self._address = address
        self._bus = bus

    def read(self, length):
        try:
            read_msg = i2c_msg.read(self._address, length)
            self._bus.i2c_rdwr(read_msg)
            return read_msg.buf[0:read_msg.len]
        except TypeError as e:
            raise TransportException(f"Error during reading I2C address 0x{self._address:X}") from e

    def write(self, data):
        try:
            write_msg = i2c_msg.write(self._address, data)
            self._bus.i2c_rdwr(write_msg)
        except TypeError as e:
            raise TransportException(f"Error during writing I2C address 0x{self._address:X}") from e


class RevvyTransportI2C:
    def __init__(self, bus):
        self._bus = SMBus(bus)

    def bind(self, address):
        return RevvyTransport(RevvyTransportI2CDevice(address, self._bus))

    def close(self):
        self._bus.close()

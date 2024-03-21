from revvy.utils.logger import get_logger, LogLevel

# ignore reason: raspberry-specific import
from smbus2 import i2c_msg, SMBus  # pyright: ignore[reportMissingImports]

from revvy.mcu.rrrc_control import RevvyTransportBase, RevvyControl, BootloaderControl
from revvy.mcu.rrrc_transport import RevvyTransportInterface, RevvyTransport, TransportException


class RevvyTransportI2CDevice(RevvyTransportInterface):
    """Low level communication class used to read/write a specific I2C device address"""

    def __init__(self, address, transport: "RevvyTransportI2C") -> None:
        self._address = address
        self._transport = transport
        self.log = get_logger(f"rrrc_transport_i2c 0x{self._address:X}")

    def read(self, length: int) -> bytes:
        try:
            read_msg = i2c_msg.read(self._address, length)
            self._transport._bus.i2c_rdwr(read_msg)
            return read_msg.buf[0 : read_msg.len]
        except TypeError as e:
            raise TransportException("Error reading I2C") from e
        except OSError as ex:
            self.log(
                f"OSError({ex.errno}) reading I2C: {ex.strerror}",
                LogLevel.DEBUG,
            )
            raise ex

    def write(self, data: bytes) -> None:
        try:
            write_msg = i2c_msg.write(self._address, data)
            self._transport._bus.i2c_rdwr(write_msg)
        except TypeError as e:
            raise TransportException("Error writing I2C") from e
        except OSError as ex:
            self.log(
                f"OSError({ex.errno}) writing I2C: {ex.strerror}",
                LogLevel.DEBUG,
            )
            raise ex


class RevvyTransportI2C(RevvyTransportBase):
    BOOTLOADER_I2C_ADDRESS = 0x2B
    ROBOT_I2C_ADDRESS = 0x2D

    def __init__(self, bus: int):
        self.log = get_logger(f"rrrc_transport_i2c bus")
        self.log(f"Opening I2C bus: {bus}", LogLevel.DEBUG)
        self._bus = SMBus(bus)

    def _bind(self, address: int) -> RevvyTransport:
        return RevvyTransport(RevvyTransportI2CDevice(address, self))

    def create_bootloader_control(self) -> BootloaderControl:
        return BootloaderControl(self._bind(self.BOOTLOADER_I2C_ADDRESS))

    def create_application_control(self) -> RevvyControl:
        return RevvyControl(self._bind(self.ROBOT_I2C_ADDRESS))

    def __del__(self) -> None:
        self.log("Closing I2C bus", LogLevel.DEBUG)
        self._bus.close()

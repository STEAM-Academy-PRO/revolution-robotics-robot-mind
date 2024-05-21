import struct
from threading import Lock
import traceback
from abc import ABC, abstractmethod
from enum import Enum
from typing import Generic, Optional, TypeVar

from revvy.utils.functions import split
from revvy.utils.logger import LogLevel, get_logger
from revvy.utils.version import Version, FormatError
from revvy.mcu.rrrc_transport import RevvyTransport, Response, ResponseStatus


class UnknownCommandError(Exception):
    pass


ReturnType = TypeVar("ReturnType")


# TODO: We can make Command a subclass of Callable, so we can have a strongly typed base __call__
# and no special-cased subclasses. Requires Python 3.11 or 12, though.
class Command(ABC, Generic[ReturnType]):
    """A generic command towards the MCU"""

    def __init__(self, transport: RevvyTransport):
        self._transport = transport
        self._command_byte = self.command_id
        # We can not differentiate between multiple calls to the same command, so we need this lock
        # to only allow one command with the same ID at a time
        self._command_lock = Lock()

        self._log = get_logger(f"{type(self).__name__} [id={hex(self._command_byte)}]")

    @property
    @abstractmethod
    def command_id(self) -> int:
        pass

    def _process(self, response: Response) -> ReturnType:
        if response.status == ResponseStatus.Ok:
            return self.parse_response(response.payload)
        elif response.status == ResponseStatus.Error_UnknownCommand:
            raise UnknownCommandError(
                f"{self.__class__.__name__} not implemented on MCU: {hex(self._command_byte)}"
            )
        else:
            raise ValueError(
                f'{self.__class__.__name__} failed with status: "{response.status}" with payload: {repr(response.payload)}'
            )

    def _send(self, payload: bytes = b"") -> ReturnType:
        """
        Send the command with the given payload and process the response

        @type payload: bytes
        """
        with self._command_lock:
            response = self._transport.send_command(self._command_byte, payload)

        try:
            return self._process(response)
        except (UnknownCommandError, ValueError) as e:
            self._log(traceback.format_exc(), LogLevel.ERROR)
            self._log(f"Command payload for error: {list(payload)}", LogLevel.ERROR)
            raise e

    @abstractmethod
    def parse_response(self, payload: bytes) -> ReturnType:
        pass


class ParameterlessCommand(Generic[ReturnType], Command[ReturnType]):
    """A command that doesn't require any parameters to be sent to the MCU.

    We don't define Command.__call__ because doing so - and overriding with more concrete call
    implementations - makes pyright unhappy"""

    def __call__(self) -> ReturnType:
        return self._send()


class ReturnlessCommand(Command[None]):
    """A command that doesn't require any parameters to be sent to the MCU.

    We don't define Command.__call__ because doing so - and overriding with more concrete call
    implementations - makes pyright unhappy"""

    def parse_response(self, payload: bytes) -> None:
        if len(payload) > 0:
            # TODO: this is a ValueError maybe, but we can also be tolerant?
            raise NotImplementedError
        return None


# The following classes implement the python counterpart of MCU commands.
# MCU commands are defined in:
# - mcu-bootloader/rrrc/runtime/comm_handlers.c
# - mcu-firmware/rrrc/runtime/comm_handlers.c
# The commands are collected in the RevvyControl and BootloaderControl classes in the rrrc_control.py
# file, providing a function call-like interface to the commands.


class PingCommand(ReturnlessCommand, ParameterlessCommand[None]):
    @property
    def command_id(self) -> int:
        return 0x00


class IMUOrientationEstimator_Reset_Command(ReturnlessCommand, ParameterlessCommand[None]):
    @property
    def command_id(self) -> int:
        return 0x41


class ReadVersionCommand(ParameterlessCommand[Optional[Version]], ABC):
    def parse_response(self, payload: bytes) -> Optional[Version]:
        try:
            return Version(parse_string(payload))
        except (UnicodeDecodeError, FormatError):
            return None


class ReadHardwareVersionCommand(ReadVersionCommand):
    @property
    def command_id(self) -> int:
        return 0x01


class ReadFirmwareVersionCommand(ReadVersionCommand):
    @property
    def command_id(self) -> int:
        return 0x02


class SetMasterStatusCommand(ReturnlessCommand, Command):
    def __init__(self, transport: RevvyTransport):
        super().__init__(transport)
        self._format = struct.Struct("B")

    @property
    def command_id(self) -> int:
        return 0x04

    def __call__(self, status: int) -> None:
        # TODO: make this accept something meaningful
        return self._send(bytes([status]))


class SetBluetoothStatusCommand(ReturnlessCommand, Command):
    @property
    def command_id(self) -> int:
        return 0x05

    def __call__(self, status: int) -> None:
        # TODO: make this accept something meaningful
        return self._send(bytes([status]))


class RebootToBootloaderCommand(ReturnlessCommand, ParameterlessCommand):
    @property
    def command_id(self) -> int:
        return 0x0B


class ReadPortTypesCommand(ParameterlessCommand[dict[str, int]], ABC):
    def parse_response(self, payload: bytes):
        return parse_string_list(payload)


class ReadMotorPortTypesCommand(ReadPortTypesCommand):
    @property
    def command_id(self) -> int:
        return 0x11


class ReadSensorPortTypesCommand(ReadPortTypesCommand):
    @property
    def command_id(self) -> int:
        return 0x21


class ReadRingLedScenarioTypesCommand(ParameterlessCommand[dict[str, int]]):
    @property
    def command_id(self) -> int:
        return 0x30

    def parse_response(self, payload: bytes) -> dict[str, int]:
        return parse_string_list(payload)


class ReadPortAmountCommand(ParameterlessCommand[int], ABC):
    def parse_response(self, payload) -> int:
        assert len(payload) == 1
        return payload[0]


class ReadMotorPortAmountCommand(ReadPortAmountCommand):
    @property
    def command_id(self) -> int:
        return 0x10


class ReadSensorPortAmountCommand(ReadPortAmountCommand):
    @property
    def command_id(self) -> int:
        return 0x20


class SetPortTypeCommand(Command[bool], ABC):
    def __call__(self, port: int, port_type_idx: int) -> bool:
        return self._send(bytes([port, port_type_idx]))

    def parse_response(self, payload: bytes) -> bool:
        return payload[0] == 1


class SetMotorPortTypeCommand(SetPortTypeCommand):
    @property
    def command_id(self) -> int:
        return 0x12


class TestSensorOnPortResult(Enum):
    NOT_CONNECTED = 0
    CONNECTED = 1
    UNKNOWN = 2
    ERROR = 3


class TestSensorOnPortCommand(Command[TestSensorOnPortResult], ABC):
    @property
    def command_id(self) -> int:
        return 0x25

    def __call__(self, port: int, port_type: int) -> TestSensorOnPortResult:
        return self._send(bytes([port, port_type]))

    def parse_response(self, payload: bytes) -> TestSensorOnPortResult:
        raw_response = payload[0]
        response = TestSensorOnPortResult(raw_response)
        self._log(f"TestSensorOnPortCommand:resp: {payload}, {response} ({raw_response})")
        return response


class TestMotorOnPortCommand(Command[bool], ABC):
    @property
    def command_id(self) -> int:
        return 0x15

    def __call__(self, port, test_intensity, threshold) -> bool:
        payload = bytes([port, test_intensity, threshold])
        return self._send(payload)

    def parse_response(self, payload: bytes) -> bool:
        return payload[0] != 0


class SetSensorPortTypeCommand(SetPortTypeCommand):
    @property
    def command_id(self) -> int:
        return 0x22


class SetRingLedScenarioCommand(ReturnlessCommand):
    @property
    def command_id(self) -> int:
        return 0x31

    def __call__(self, scenario_idx: int) -> None:
        return self._send(bytes([scenario_idx]))


class GetRingLedAmountCommand(ParameterlessCommand[int]):
    @property
    def command_id(self) -> int:
        return 0x32

    def parse_response(self, payload: bytes):
        assert len(payload) == 1
        return int(payload[0])


class SendRingLedUserFrameCommand(ReturnlessCommand):
    @property
    def command_id(self) -> int:
        return 0x33

    def __call__(self, colors: list[int]) -> None:
        rgb565_values = map(rgb_to_rgb565_bytes, colors)
        led_bytes = struct.pack(f"<{len(colors)}H", *rgb565_values)
        return self._send(led_bytes)


class SetPortConfigCommand(ReturnlessCommand, ABC):
    def __call__(self, port_idx: int, config: bytes) -> None:
        # TODO: can we do something nicer? I.e. specify the config type in this module, serialize here?
        return self._send(bytes([port_idx, *config]))


class SetMotorPortConfigCommand(SetPortConfigCommand):
    @property
    def command_id(self) -> int:
        return 0x13


class WriteSensorPortCommand(SetPortConfigCommand):
    @property
    def command_id(self) -> int:
        return 0x23


class ReadSensorPortInfoCommand(Command[bytes]):
    @property
    def command_id(self) -> int:
        return 0x24

    def __call__(self, port_idx: int, page: int = 0) -> bytes:
        return self._send(bytes([port_idx, page]))

    def parse_response(self, payload: bytes):
        return payload


class SetMotorPortControlCommand(Command[bytes]):
    @property
    def command_id(self) -> int:
        return 0x14

    def __call__(self, command_bytes: bytes):
        if len(command_bytes) == 0:
            # special-case the "no command", because we can't differentiate between an error
            # and a successful "no command"
            return bytes()
        return self._send(command_bytes)

    def parse_response(self, payload: bytes) -> bytes:
        # this command returns as many bytes as there were commands batched
        if len(payload) == 0:
            # we don't know the failure, we just get an empty response
            raise ValueError("Failed to send motor control command")
        return payload


class ReadPortStatusCommand(Command, ABC):
    def __call__(self, port_idx: int) -> bytes:
        return self._send(bytes([port_idx]))

    def parse_response(self, payload: bytes) -> bytes:
        """Return the raw response"""
        return payload


class McuStatusUpdater_ResetCommand(ReturnlessCommand, ParameterlessCommand):
    @property
    def command_id(self) -> int:
        return 0x3A


class McuStatusUpdater_ControlCommand(ReturnlessCommand):
    @property
    def command_id(self) -> int:
        return 0x3B

    def __call__(self, slot: int, is_enabled: bool) -> None:
        return self._send(bytes([slot, is_enabled]))


class McuStatusUpdater_ReadCommand(ParameterlessCommand[bytes]):
    @property
    def command_id(self) -> int:
        return 0x3C

    def parse_response(self, payload: bytes) -> bytes:
        """Return the raw response"""
        return payload


class ErrorMemory_ReadCount(ParameterlessCommand[int]):
    @property
    def command_id(self) -> int:
        return 0x3D

    def parse_response(self, payload: bytes) -> int:
        assert len(payload) == 4
        return int.from_bytes(payload, byteorder="little")


class ErrorMemory_ReadErrors(Command[list[bytes]]):
    @property
    def command_id(self) -> int:
        return 0x3E

    def __call__(self, start_idx: int = 0):
        return self._send(start_idx.to_bytes(4, byteorder="little"))

    def parse_response(self, payload: bytes):
        return list(split(payload, 63))


class ErrorMemory_Clear(ReturnlessCommand, ParameterlessCommand):
    @property
    def command_id(self) -> int:
        return 0x3F


class ErrorMemory_TestError(ReturnlessCommand, ParameterlessCommand):
    @property
    def command_id(self) -> int:
        return 0x40


# Bootloader-specific commands:
class ReadFirmwareCrcCommand(ParameterlessCommand[int]):
    @property
    def command_id(self) -> int:
        return 0x07

    def parse_response(self, payload: bytes) -> int:
        return int.from_bytes(payload, byteorder="little")


class InitializeUpdateCommand(ReturnlessCommand):
    def __init__(self, transport: RevvyTransport):
        super().__init__(transport)
        self._format = struct.Struct("<LL")

    @property
    def command_id(self) -> int:
        return 0x08

    def __call__(self, crc, length) -> None:
        return self._send(self._format.pack(crc, length))


class SendFirmwareCommand(ReturnlessCommand):
    @property
    def command_id(self) -> int:
        return 0x09

    def __call__(self, data: bytes) -> None:
        return self._send(data)


class FinalizeUpdateCommand(ReturnlessCommand, ParameterlessCommand):
    @property
    def command_id(self) -> int:
        return 0x0A


def parse_string(data: bytes, ignore_errors=False) -> str:
    """
    >>> parse_string(b'foobar')
    'foobar'
    >>> parse_string(b'foo\\xffbar', ignore_errors=True)
    'foobar'
    """
    return data.decode("utf-8", errors="ignore" if ignore_errors else "strict")


def parse_string_list(data: bytes) -> dict[str, int]:
    """
    >>> parse_string_list(b'\x01\x06foobar')
    {'foobar': 1}
    >>> parse_string_list(b'\x01\x06foobar\x02\x03baz')
    {'foobar': 1, 'baz': 2}
    """
    val = {}
    idx = 0
    while idx < len(data):
        data_start = idx + 2
        key, length = data[idx:data_start]
        idx = data_start + length

        name = parse_string(data[data_start : data_start + length])

        val[name] = key
    return val


def rgb_to_rgb565_bytes(rgb: int) -> int:
    """
    Convert 24bit color to 16bit

    >>> rgb_to_rgb565_bytes(0)
    0
    >>> rgb_to_rgb565_bytes(0x800000)
    32768
    >>> rgb_to_rgb565_bytes(0x080408)
    2081
    >>> rgb_to_rgb565_bytes(0x808080)
    33808
    >>> rgb_to_rgb565_bytes(0xFFFFFF)
    65535
    """
    r = (rgb & 0x00F80000) >> 8
    g = (rgb & 0x0000FC00) >> 5
    b = (rgb & 0x000000F8) >> 3

    return r | g | b

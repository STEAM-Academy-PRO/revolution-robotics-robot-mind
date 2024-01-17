# SPDX-License-Identifier: GPL-3.0-only

import struct
import traceback
from abc import ABC
from collections import namedtuple
from enum import Enum

from revvy.utils.functions import split
from revvy.utils.logger import get_logger
from revvy.utils.version import Version, FormatError
from revvy.mcu.rrrc_transport import RevvyTransport, Response, ResponseStatus


class UnknownCommandError(Exception):
    pass


class Command:
    """A generic command towards the MCU"""

    def __init__(self, transport: RevvyTransport):
        self._transport = transport
        self._command_byte = self.command_id

        self._log = get_logger(f'{type(self).__name__} [id={self._command_byte}]')

    @property
    def command_id(self):
        raise NotImplementedError

    def _process(self, response: Response):
        if response.status == ResponseStatus.Ok:
            return self.parse_response(response.payload)
        elif response.status == ResponseStatus.Error_UnknownCommand:
            raise UnknownCommandError(f"Command not implemented: {self._command_byte}")
        else:
            raise ValueError(f'Command status: "{response.status}" with payload: {repr(response.payload)}')

    def _send(self, payload=b'', get_result_delay=None):
        """
        Send the command with the given payload and process the response

        @type payload: iterable
        """
        response = self._transport.send_command(self._command_byte,
            payload, get_result_delay)

        try:
            return self._process(response)
        except (UnknownCommandError, ValueError) as e:
            self._log(f'Payload for error: {payload} (length {len(payload)})')
            self._log(traceback.format_exc())
            raise e

    def __call__(self, *args):
        if args:
            raise NotImplementedError

        return self._send()

    def parse_response(self, payload):
        if payload:
            raise NotImplementedError

        return None


class PingCommand(Command):
    @property
    def command_id(self): return 0x00


class IMUOrientationEstimator_Reset_Command(Command):
    @property
    def command_id(self): return 0x41


class ReadVersionCommand(Command, ABC):
    def parse_response(self, payload):
        try:
            return Version(parse_string(payload))
        except (UnicodeDecodeError, FormatError):
            return None


class ReadHardwareVersionCommand(ReadVersionCommand):
    @property
    def command_id(self): return 0x01


class ReadFirmwareVersionCommand(ReadVersionCommand):
    @property
    def command_id(self): return 0x02


BatteryStatus = namedtuple('BatteryStatus',
    ['chargerStatus', 'motor_battery_present', 'main', 'motor'])


class SetMasterStatusCommand(Command):
    @property
    def command_id(self): return 0x04

    def __call__(self, status):
        # TODO: make this accept something meaningful
        return self._send((status, ))


class SetBluetoothStatusCommand(Command):
    @property
    def command_id(self): return 0x05

    def __call__(self, status):
        # TODO: make this accept something meaningful
        return self._send((status, ))


class McuOperationMode(Enum):
    APPLICATION = 0xAA
    BOOTLOADER = 0xBB


class ReadOperationModeCommand(Command):
    @property
    def command_id(self): return 0x06

    def parse_response(self, payload):
        assert len(payload) == 1
        return McuOperationMode(payload[0])


class RebootToBootloaderCommand(Command):
    @property
    def command_id(self): return 0x0B


class ReadPortTypesCommand(Command, ABC):
    def parse_response(self, payload):
        return parse_string_list(payload)


class ReadMotorPortTypesCommand(ReadPortTypesCommand):
    @property
    def command_id(self): return 0x11


class ReadSensorPortTypesCommand(ReadPortTypesCommand):
    @property
    def command_id(self): return 0x21


class ReadRingLedScenarioTypesCommand(Command):
    @property
    def command_id(self): return 0x30

    def parse_response(self, payload):
        return parse_string_list(payload)


class ReadPortAmountCommand(Command, ABC):
    def parse_response(self, payload):
        assert len(payload) == 1
        return int(payload[0])


class ReadMotorPortAmountCommand(ReadPortAmountCommand):
    @property
    def command_id(self): return 0x10


class ReadSensorPortAmountCommand(ReadPortAmountCommand):
    @property
    def command_id(self): return 0x20


class SetPortTypeCommand(Command, ABC):
    def __call__(self, port, port_type_idx):
        return self._send((port, port_type_idx))


class SetMotorPortTypeCommand(SetPortTypeCommand):
    @property
    def command_id(self): return 0x12

class TestSensorOnPortResult:
    def __init__(self, result_code):
        self.__result_code = result_code

    def __stringify(self):
        if self.__result_code == 0:
            return 'NOT_CONNECTED'
        if self.__result_code == 1:
            return 'CONNECTED'
        if self.__result_code == 2:
            return 'UNKNOWN'
        if self.__result_code == 3:
            return 'ERROR'
        return "INVALID"

    def __str__(self):
        return self.__stringify()

    def __repr__(self):
        return self.__stringify()

    def is_not_connected(self):
        return self.__result_code == 0

    def is_connected(self):
        return self.__result_code == 1

    def is_unknown(self):
        return self.__result_code == 2

    def is_error(self):
        return self.__result_code == 3


class TestSensorOnPortCommand(Command, ABC):
    @property
    def command_id(self):
        return 0x25

    def __call__(self, port, port_type):
        payload = struct.pack('BB', port, port_type)
        return self._send((payload))

    def parse_response(self, payload):
        response = struct.unpack('b', payload)[0]
        response = TestSensorOnPortResult(response)
        self._log('TestSensorOnPortCommand:resp: {},{}'.format(
          payload, response))
        return response

class TestMotorOnPortCommand(Command, ABC):
    @property
    def command_id(self):
        return 0x15

    def __call__(self, port, test_intensity, threshold):
        # For test motor on port GetResult transfer phase should start
        # after a small delay (I2C BUG workaround), other commands should
        # behave as before
        get_result_delay = 0.2
        payload = struct.pack('BBB', port, test_intensity, threshold)
        return self._send((payload), get_result_delay)

    def parse_response(self, payload):
        motor_is_present = struct.unpack('b', payload)[0] != 0
        return motor_is_present


class SetSensorPortTypeCommand(SetPortTypeCommand):
    @property
    def command_id(self): return 0x22


class SetRingLedScenarioCommand(Command):
    @property
    def command_id(self): return 0x31

    def __call__(self, scenario_idx):
        return self._send((scenario_idx, ))


class GetRingLedAmountCommand(Command):
    @property
    def command_id(self): return 0x32

    def parse_response(self, payload):
        assert len(payload) == 1
        return int(payload[0])


class SendRingLedUserFrameCommand(Command):
    @property
    def command_id(self): return 0x33

    def __call__(self, colors):
        rgb565_values = map(rgb_to_rgb565_bytes, colors)
        led_bytes = struct.pack(f"<{len(colors)}H", *rgb565_values)
        return self._send(led_bytes)


class SetPortConfigCommand(Command, ABC):
    def __call__(self, port_idx, config):
        return self._send((port_idx, *config))


class SetMotorPortConfigCommand(SetPortConfigCommand):
    @property
    def command_id(self): return 0x13


class WriteSensorPortCommand(SetPortConfigCommand):
    @property
    def command_id(self): return 0x23


class ReadSensorPortInfoCommand(Command):
    @property
    def command_id(self): return 0x24

    def __call__(self, port_idx, page=0):
        val = self._send((port_idx, page))
        return val

    def parse_response(self, payload):
        return payload


class SetMotorPortControlCommand(Command):
    @property
    def command_id(self): return 0x14

    def __call__(self, command_bytes: bytes):
        val = self._send(command_bytes)
        return val


class ReadPortStatusCommand(Command, ABC):
    def __call__(self, port_idx):
        return self._send((port_idx, ))

    def parse_response(self, payload):
        """Return the raw response"""
        return payload


class McuStatusUpdater_ResetCommand(Command):
    @property
    def command_id(self): return 0x3A


class McuStatusUpdater_ControlCommand(Command):
    @property
    def command_id(self): return 0x3B

    def __call__(self, slot, is_enabled: bool):
        return self._send((slot, is_enabled))


class McuStatusUpdater_ReadCommand(Command):
    @property
    def command_id(self): return 0x3C

    def parse_response(self, payload):
        """Return the raw response"""
        return payload


class ErrorMemory_ReadCount(Command):
    @property
    def command_id(self): return 0x3D

    def parse_response(self, payload):
        assert len(payload) == 4
        return int.from_bytes(payload, byteorder='little')


class ErrorMemory_ReadErrors(Command):
    @property
    def command_id(self): return 0x3E

    def __call__(self, start_idx=0):
        return self._send(start_idx.to_bytes(4, byteorder='little'))

    def parse_response(self, payload):
        return list(split(payload, 63))


class ErrorMemory_Clear(Command):
    @property
    def command_id(self): return 0x3F


class ErrorMemory_TestError(Command):
    @property
    def command_id(self): return 0x40


# Bootloader-specific commands:
class ReadFirmwareCrcCommand(Command):
    @property
    def command_id(self): return 0x07

    def parse_response(self, payload):
        return int.from_bytes(payload, byteorder="little")


class InitializeUpdateCommand(Command):
    @property
    def command_id(self): return 0x08

    def __call__(self, crc, length):
        return self._send(struct.pack("<LL", crc, length))


class SendFirmwareCommand(Command):
    @property
    def command_id(self): return 0x09

    def __call__(self, data):
        return self._send(data)


class FinalizeUpdateCommand(Command):
    @property
    def command_id(self): return 0x0A


def parse_string(data, ignore_errors=False):
    """
    >>> parse_string(b'foobar')
    'foobar'
    >>> parse_string(b'foo\\xffbar', ignore_errors=True)
    'foobar'
    """
    return data.decode('utf-8', errors='ignore' if ignore_errors else 'strict')


def parse_string_list(data):
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

        name = parse_string(data[data_start:data_start + length])

        val[name] = key
    return val


def rgb_to_rgb565_bytes(rgb):
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

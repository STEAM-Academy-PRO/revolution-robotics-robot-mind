# TODO: this probably isn't the best place
import abc
from enum import Enum
import enum
import struct
from typing import Any
from revvy.utils.bit_packer import pack_2_bit_number_array_32
from revvy.utils.logger import get_logger
from revvy.utils.math.floor0 import floor0
from revvy.utils.serialize import Serialize


class GyroData:
    """A 3D vector"""

    def __init__(self, a: float, b: float, c: float):
        self.a = floor0(a, 1)
        self.b = floor0(b, 1)
        self.c = floor0(c, 1)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GyroData):
            return False

        # These values are rounded to the first decimal so we can compare them directly
        return other.a == self.a and other.b == self.b and other.c == self.c

    def __json__(self) -> dict:
        return {"a": self.a, "b": self.b, "c": self.c}

    def __bytes__(self) -> bytes:
        return struct.pack("fff", self.a, self.b, self.c)


class ProgramStatusCollection:
    def __init__(self) -> None:
        self._states = [0] * 32
        self._log = get_logger("ProgramStatusCollection")

    def update_button_value(self, button_id: int, status: int):
        self._log(f"button state array id:{button_id} => stat: {status}")
        self._states[button_id] = status

    def __bytes__(self) -> bytes:
        return pack_2_bit_number_array_32(self._states)


class ScriptVariables:
    def __init__(self, variables: list):
        self.script_variables = variables

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, ScriptVariables):
            return __value.script_variables == self.script_variables
        return False

    def __bytes__(self) -> bytes:
        # I believe this should be a constant that's coming from one centralized place, rather
        # be wired in here. If this script sends more variables, we'll never know.
        MAX_VARIABLE_SLOTS = 4

        # Message format:
        # offset:  0    1  2  3  4    5  6  7  8    9  10 11 12   13 14 15 16
        # values:  0A | BB BB BB BB | CC CC CC CC | DD DD DD DD | EE EE EE EE
        # A - bitmask consists of 4 bits. if bit is set - value has been set
        #     by scripts. If bit is not set - value has never been changed yet,
        #     due to script not run at all, or script has not yet set the value
        #     and ReportVariableChanged has not been called for this slot

        # BB - float value for Slot 1
        # CC - float value for Slot 2
        # DD - float value for Slot 3
        # EE - float value for Slot 4

        # In the end the user of this packet receives info about 4 slots, current
        # value of each slot, has the value in this slot been set at least once

        mask = 0
        valuebuf = b""

        for slot_idx in range(MAX_VARIABLE_SLOTS):
            value = self.script_variables[slot_idx]
            if value:
                mask = mask | (1 << slot_idx)
            else:
                value = 0.0
            valuebuf += struct.pack("f", value)

        maskbuf = struct.pack("B", mask)
        msg = maskbuf + valuebuf

        return msg


class TimerData:
    def __init__(self, value) -> None:
        self.value = value

    def __bytes__(self) -> bytes:
        return struct.pack(">bf", 4, round(self.value, 0))


class BackgroundControlState(Enum):
    STOPPED = 1
    RUNNING = 2
    PAUSED = 3

    def __state_to_str(self) -> str:
        if self == BackgroundControlState.STOPPED:
            return "bg_state:stopped"
        if self == BackgroundControlState.RUNNING:
            return "bg_state:running"
        if self == BackgroundControlState.PAUSED:
            return "bg_state:paused"
        return "bg_state:undefined"

    def __str__(self) -> str:
        return self.__state_to_str()

    def __repr__(self) -> str:
        return self.__state_to_str()

    def __bytes__(self) -> bytes:
        # TODO: what's 4, and why do we specify big endian here?
        return struct.pack(">bl", 4, self.value)


# TODO: make this a base class for sensors to implement
class SensorData(Serialize):
    def __init__(self, port_id: int, value: Any):
        self.port_id = port_id
        self.value = value

    def __json__(self) -> dict:
        return {"port_id": self.port_id, "value": self.value}

    def __bytes__(self) -> bytes:
        return self.value


class UltrasonicSensorData(SensorData):
    def __bytes__(self) -> bytes:
        return round(self.value).to_bytes(2, "little") + b"\x00\x00"


class BumperSensorData(SensorData):
    def __bytes__(self) -> bytes:
        return b"\x01" if self.value else b"\x00"


class ColorSensorData(SensorData):
    def __bytes__(self) -> bytes:
        # TODO: this does not belong here. But I do know where it does.
        # Where should complex type serialization go?
        return self.value.__bytes__()

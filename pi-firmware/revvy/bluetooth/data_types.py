# TODO: this probably isn't the best place
import abc
from enum import Enum
import enum
import struct
from revvy.utils.bit_packer import pack_2_bit_number_array_32
from revvy.utils.logger import get_logger
from revvy.utils.serialize import Serialize


class MotorData(Serialize):
    def __init__(self, speed, position, power):
        self.position = position
        self.speed = speed
        self.power = power

    def serialize(self):
        return struct.pack(">flb", self.speed, self.position, self.power)


class GyroData(Serialize):
    """A 3D vector"""

    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c

    def serialize(self):
        return struct.pack("fff", self.a, self.b, self.c)


class ProgramStatusCollection(Serialize):
    def __init__(self):
        self._states = [0] * 32
        self._log = get_logger("ProgramStatusCollection")

    def update_button_value(self, button_id: int, status: int):
        self._log(f"button state array id:{button_id} => stat: {status}")
        self._states[button_id] = status

    def serialize(self):
        return pack_2_bit_number_array_32(self._states)


class ScriptVariables(Serialize):
    def __init__(self, variables: list):
        self.script_variables = variables

    def serialize(self):
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


class TimerData(Serialize):
    def __init__(self, value):
        self.value = value

    def serialize(self):
        return struct.pack(">bf", 4, round(self.value, 0))


class ABCEnumMeta(abc.ABCMeta, enum.EnumMeta):
    # We need this metaclass to allow Serialize and Enum on the same type
    # https://stackoverflow.com/a/56135108
    def __new__(mcls, *args, **kw):
        abstract_enum_cls = super().__new__(mcls, *args, **kw)
        # Only check abstractions if members were defined.
        if abstract_enum_cls._member_map_:
            try:  # Handle existence of undefined abstract methods.
                absmethods = list(abstract_enum_cls.__abstractmethods__)
                if absmethods:
                    missing = ", ".join(f"{method!r}" for method in absmethods)
                    plural = "s" if len(absmethods) > 1 else ""
                    raise TypeError(
                        f"cannot instantiate abstract class {abstract_enum_cls.__name__!r}"
                        f" with abstract method{plural} {missing}"
                    )
            except AttributeError:
                pass
        return abstract_enum_cls


class BackgroundControlState(Serialize, Enum, metaclass=ABCEnumMeta):
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

    def serialize(self):
        # TODO: what's 4, and why do we specify big endian here?
        return struct.pack(">bl", 4, self.value)


# TODO: make this a base class for sensors to implement
class SensorData(Serialize):
    def __init__(self, value):
        self.value = value

    def serialize(self):
        return self.value

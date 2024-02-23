import struct
from typing import NamedTuple

from revvy.robot.ports.common import PortInstance
from revvy.robot.ports.sensors.base import SensorPortDriver
from revvy.utils.logger import get_logger

log = get_logger("SensorDataConverter")


class BumperSwitch(SensorPortDriver):
    def __init__(self, port: PortInstance[SensorPortDriver], config):
        super().__init__(port, "BumperSwitch")

    def convert_sensor_value(self, raw):
        assert len(raw) == 2
        return raw[0] == 1


class Hcsr04(SensorPortDriver):
    def __init__(self, port: PortInstance[SensorPortDriver], config):
        super().__init__(port, "HC_SR04")

    def convert_sensor_value(self, raw):
        assert len(raw) == 4
        (dst,) = struct.unpack("<l", raw)
        if dst == 0:
            return None
        return dst


class ColorSensor(SensorPortDriver):
    def __init__(self, port: PortInstance[SensorPortDriver], config):
        super().__init__(port, "RGB")

    def convert_sensor_value(self, raw: bytearray):
        # 12 bytes: 4 sensors, RGB
        if len(raw) == 12:
            return ColorSensorReading(raw)
        else:
            return ColorSensorReading(b"\x00" * 12)


class Color(NamedTuple):
    r: bytes
    g: bytes
    b: bytes


color_from_bytes = lambda bytes: Color(bytes[0], bytes[1], bytes[2])


class ColorSensorReading:
    """
    Facing sensor side (LEDs poking your eyes side):

             [TOP]

    [LEFT] [MIDDLE] [RIGHT]

    """

    def __init__(self, byte_array: bytes = None):
        if byte_array is None:
            byte_array = b"\x00" * 12
        self.top: Color = color_from_bytes(byte_array[0:3])
        self.right: Color = color_from_bytes(byte_array[3:6])
        self.left: Color = color_from_bytes(byte_array[6:9])
        self.middle: Color = color_from_bytes(byte_array[9:12])

    def serialize(self):
        byte_array = bytearray()
        for color in [self.top, self.right, self.left, self.middle]:
            byte_array.extend([color.r, color.g, color.b])
        return byte_array

    def __str__(self):
        """This is really just for debugging."""
        ret = f"Top: {self.top.r}, {self.top.g}, {self.top.b} "
        ret += f"Left: {self.left.r}, {self.left.g}, {self.left.b} "
        ret += f"Right: {self.right.r}, {self.right.g}, {self.right.b} "
        ret += f"Middle: {self.middle.r}, {self.middle.g}, {self.middle.b}"
        return ret

    def __json__(self):
        return {
            "top": {"r": self.top.r, "g": self.top.g, "b": self.top.b},
            "right": {"r": self.right.r, "g": self.right.g, "b": self.right.b},
            "left": {"r": self.left.r, "g": self.left.g, "b": self.left.b},
            "middle": {"r": self.middle.r, "g": self.middle.g, "b": self.middle.b},
        }

from typing import NamedTuple

from revvy.robot.ports.common import PortInstance
from revvy.robot.ports.sensors.base import SensorPortDriver
from revvy.utils.logger import get_logger

log = get_logger("SensorDataConverter")


class BumperSwitch(SensorPortDriver):
    def __init__(self, port: PortInstance[SensorPortDriver], config):
        super().__init__(port, "BumperSwitch")

    def convert_sensor_value(self, raw: bytes):
        assert len(raw) == 2
        return raw[0] == 1


class Hcsr04(SensorPortDriver):
    def __init__(self, port: PortInstance[SensorPortDriver], config):
        super().__init__(port, "HC_SR04")

    def convert_sensor_value(self, raw: bytes):
        assert len(raw) == 4
        dst = int.from_bytes(raw, "little")
        if dst == 0:
            return None
        return dst


class ColorSensor(SensorPortDriver):
    def __init__(self, port: PortInstance[SensorPortDriver], config):
        super().__init__(port, "RGB")

    def convert_sensor_value(self, raw: bytes):
        # 12 bytes: 4 sensors, RGB
        if len(raw) == 12:
            return ColorSensorReading(raw)
        else:
            return ColorSensorReading(b"\x00" * 12)


class Color(NamedTuple):
    r: int
    g: int
    b: int

    @staticmethod
    def from_bytes(bytes: bytes) -> "Color":
        return Color(bytes[0], bytes[1], bytes[2])

    def __str__(self) -> str:
        return f"{self.r}, {self.g}, {self.b}"

    def __json__(self) -> dict:
        return {"r": self.r, "g": self.g, "b": self.b}


class ColorSensorReading:
    """
    Facing sensor side (LEDs poking your eyes side):

             [TOP]

    [LEFT] [MIDDLE] [RIGHT]

    """

    def __init__(self, byte_array: bytes):
        self.top = Color.from_bytes(byte_array[0:3])
        self.right = Color.from_bytes(byte_array[3:6])
        self.left = Color.from_bytes(byte_array[6:9])
        self.middle = Color.from_bytes(byte_array[9:12])

    def __bytes__(self) -> bytearray:
        byte_array = bytearray()
        for color in [self.top, self.right, self.left, self.middle]:
            byte_array.append(color.r)
            byte_array.append(color.g)
            byte_array.append(color.b)
        return byte_array

    def __str__(self) -> str:
        """This is really just for debugging."""
        ret = f"Top: {self.top} "
        ret += f"Left: {self.left} "
        ret += f"Right: {self.right} "
        ret += f"Middle: {self.middle}"
        return ret

    def __json__(self) -> dict:
        return {
            "top": self.top.__json__(),
            "right": self.right.__json__(),
            "left": self.left.__json__(),
            "middle": self.middle.__json__(),
        }

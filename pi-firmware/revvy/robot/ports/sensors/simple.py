import struct

from revvy.robot.ports.common import PortInstance
from revvy.robot.ports.sensors.base import SensorPortDriver

class BumperSwitch(SensorPortDriver):
    def __init__(self, port: PortInstance[SensorPortDriver], config):
        super().__init__(port, 'BumperSwitch')

    def convert_sensor_value(self, raw):
        assert len(raw) == 2
        return raw[0] == 1


class Hcsr04(SensorPortDriver):
    def __init__(self, port: PortInstance[SensorPortDriver], config):
        super().__init__(port, 'HC_SR04')

    def convert_sensor_value(self, raw):
        assert len(raw) == 4
        (dst, ) = struct.unpack("<l", raw)
        if dst == 0:
            return None
        return dst


class ColorSensor(SensorPortDriver):
    def __init__(self, port: PortInstance[SensorPortDriver], config):
        super().__init__(port, 'RGB')

    def convert_sensor_value(self, raw):
        return raw

# SPDX-License-Identifier: GPL-3.0-only

import struct

from revvy.robot.ports.common import PortInstance
from revvy.robot.ports.sensors.base import BaseSensorPortDriver


# noinspection PyUnusedLocal
def bumper_switch(port: PortInstance, cfg):
    sensor = BaseSensorPortDriver('BumperSwitch', port)
    # print("\n !!!bumper!!!\n")

    def process_bumper(raw):
        # print("bumper info:", len(raw), raw)
        assert len(raw) == 2
        return raw[0] == 1

    sensor.convert_sensor_value = process_bumper
    return sensor


# noinspection PyUnusedLocal
def hcsr04(port: PortInstance, cfg):
    sensor = BaseSensorPortDriver('HC_SR04', port)

    def process_ultrasonic(raw):

        assert len(raw) == 4
        (dst, ) = struct.unpack("<l", raw)
        # print("hcsr info:", len(raw), raw, dst)
        if dst == 0:
            return None
        return dst

    sensor.convert_sensor_value = process_ultrasonic
    return sensor


# noinspection PyUnusedLocal
def softeq_cs(port: PortInstance, cfg):
    sensor = BaseSensorPortDriver('RGB', port)
    # print("\n !!!color sensor!!!\n")

    def process_softeq_cs(raw):
        return raw

    sensor.convert_sensor_value = process_softeq_cs
    return sensor


class ColorRGB:
    def __init__(self, color_red, color_green, color_blue):
        self._name = 'softeq_cs'
        self._color_red = color_red
        self._color_green = color_green
        self._color_blue = color_blue

    @property
    def name(self):
        return self._name

    @property
    def color_red(self):
        return self._color_red

    @property
    def color_green(self):
        return self._color_green

    @property
    def color_blue(self):
        return self._color_blue

    @property
    def rgb(self):
        return struct.pack('<hhh', self._color_red, self._color_green, self._color_blue)

    def __str__(self) -> bytes:
        return self.rgb

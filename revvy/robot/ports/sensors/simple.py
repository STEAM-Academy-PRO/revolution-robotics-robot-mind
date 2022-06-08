# SPDX-License-Identifier: GPL-3.0-only

import struct

from revvy.robot.ports.common import PortInstance
from revvy.robot.ports.sensors.base import BaseSensorPortDriver


# noinspection PyUnusedLocal
def bumper_switch(port: PortInstance, cfg):
    sensor = BaseSensorPortDriver('BumperSwitch', port)
    print("\n !!!bumper!!!\n")

    def process_bumper(raw):
        print("bumper info:", len(raw), raw)
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
    print("\n !!!color sensor!!!\n")

    def process_softeq_cs(raw):
        # my_hex = raw
        # print(" ".join(hex(n) for n in my_hex))
        # assert len(raw) == 37# 8
        # color_red, color_green, color_blue, color_c = struct.unpack("<hhhh", raw)
        # if color_red == 0 and color_green == 0 and color_blue == 0:
        #     return None
        # print("0,215,0", rgb_to_hsv(0, 215, 0))
        # he = struct.iter_unpack("<BBB", my_hex)

        # for _ in struct.iter_unpack("<BBB", raw):
        #     (r, g, b) = _
        #     print("hhh ", r, g, b, *_, rgb_to_hsv(*_))

        # li = [rgb_to_hsv(*_) for _ in struct.iter_unpack("<BBB", raw)]
        # back = round(li[0][0], 1)
        # right = round(li[1][0], 1)
        # left = round(li[2][0], 1)
        # forward = round(li[3][0], 1)
        # print(back, right, left, forward)

        # ColorRGB(color_red, color_green, color_blue, color_c)
        return raw  # bytes("None1234567890None", "UTF-8")  # ColorRGB(color_red, color_green, color_blue, color_c)

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

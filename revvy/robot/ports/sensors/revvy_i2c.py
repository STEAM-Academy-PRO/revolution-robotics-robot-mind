# SPDX-License-Identifier: GPL-3.0-only
import struct
from enum import Enum

from typing import NamedTuple

from revvy.robot.ports.common import PortInstance
from revvy.robot.ports.sensors.base import BaseSensorPortDriver


class RevvyI2CSensorState(Enum):
    STATE_ERROR = 0
    STATE_RESET = 1
    STATE_DETECTED_BOOTLOADER = 2
    STATE_DETECTED_FIRMWARE = 3
    STATE_OPERATIONAL = 4


class BaseRevvyI2CSensor(BaseSensorPortDriver):
    WRITE_SENSOR_ADDRESS = 0
    WRITE_SELECT_SENSOR_MODE = 1

    def __init__(self, sensor_address, port: PortInstance, mode):
        super().__init__("RevvyI2C", port)
        assert 0 <= sensor_address <= 255, f"Invalid I2C sensor address {sensor_address}"
        self._mode = mode
        self._sensor_address = sensor_address

    def on_port_type_set(self):
        self.log(f'Setting sensor address {self._sensor_address:X}')
        self._interface.write_sensor_port(self._port.id, (self.WRITE_SENSOR_ADDRESS, self._sensor_address))

    def convert_sensor_value(self, data):
        state = RevvyI2CSensorState(data[0])

        if state == RevvyI2CSensorState.STATE_DETECTED_FIRMWARE:
            self.log('Setting sensor mode ' + self._mode)
            self._interface.write_sensor_port(self._port.id, (self.WRITE_SELECT_SENSOR_MODE, self._mode))
        elif state == RevvyI2CSensorState.STATE_OPERATIONAL:
            return self.convert_sensor_data(data)
        else:
            self.log(state)

    def convert_sensor_data(self, data):
        raise NotImplementedError


class Color(Enum):
    NONE = 0
    BLACK = 1
    BLUE = 2
    GREEN = 3
    YELLOW = 4
    CYAN = 5
    RED = 6
    WHITE = 7
    PURPLE = 8


class ColorSensorData(NamedTuple):
    line_pos: int
    color: Color


null_color = ColorSensorData(0, Color.NONE)


def revvy_color_sensor(port: PortInstance, _):
    sensor = BaseRevvyI2CSensor(0xC0, port, mode=1)
    sensor.log('Creating Revolution Robotics Color Sensor')

    def convert_color_sensor_data(data):
        if len(data) > 2:
            state, mode, line_pos, color = struct.unpack('<4b', data)

            return ColorSensorData(line_pos, Color(color))
        else:
            sensor.log('Invalid data received')
            return null_color

    sensor.convert_sensor_data = convert_color_sensor_data

    return sensor

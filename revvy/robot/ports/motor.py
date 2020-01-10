# SPDX-License-Identifier: GPL-3.0-only

from collections import namedtuple

import math

from revvy.mcu.rrrc_control import RevvyControl
from revvy.robot.ports.common import PortHandler, PortInstance
import struct

from revvy.utils.functions import clip
from revvy.utils.logger import get_logger

DcMotorStatus = namedtuple("DcMotorStatus", ['position', 'speed', 'power'])


def create_motor_port_handler(interface: RevvyControl, configs: dict):
    port_amount = interface.get_motor_port_amount()
    port_types = interface.get_motor_port_types()

    drivers = {
        'NotConfigured': NullMotor,
        'DcMotor': DcMotorController
    }
    handler = PortHandler(interface, configs, drivers, port_amount, port_types)
    handler._set_port_type = interface.set_motor_port_type

    return handler


class NullMotor:
    def __init__(self, port: PortInstance, port_config):
        self.driver = 'NotConfigured'

    def on_port_type_set(self):
        pass

    def on_status_changed(self, cb):
        pass

    @property
    def speed(self):
        return 0

    @property
    def position(self):
        return 0

    @property
    def power(self):
        return 0

    @property
    def is_moving(self):
        return False

    def set_speed(self, speed, power_limit=None):
        pass

    def set_position(self, position: int, speed_limit=None, power_limit=None, pos_type='absolute'):
        pass

    def set_power(self, power):
        pass

    def update_status(self, data):
        pass

    def get_status(self):
        return DcMotorStatus(position=0, speed=0, power=0)


class DcMotorController:
    """Generic driver for dc motors"""
    def __init__(self, port: PortInstance, port_config):
        self.driver = 'DcMotor'
        self._name = 'Motor {}'.format(port.id)
        self._port = port
        self._port_config = port_config
        self._log = get_logger(self._name)

        self._configure = lambda cfg: port.interface.set_motor_port_config(port.id, cfg)
        self._read = lambda: port.interface.get_motor_position(port.id)

        self._pos = 0
        self._speed = 0
        self._power = 0
        self._pos_reached = None

        self._status_changed_callback = None

    def on_port_type_set(self):
        (posP, posI, posD, speedLowerLimit, speedUpperLimit) = self._port_config['position_controller']
        (speedP, speedI, speedD, powerLowerLimit, powerUpperLimit) = self._port_config['speed_controller']
        (decMax, accMax) = self._port_config['acceleration_limits']

        config = []
        config += list(struct.pack("<h", self._port_config['encoder_resolution']))
        config += list(struct.pack("<{}".format("f" * 5), posP, posI, posD, speedLowerLimit, speedUpperLimit))
        config += list(struct.pack("<{}".format("f" * 5), speedP, speedI, speedD, powerLowerLimit, powerUpperLimit))
        config += list(struct.pack("<ff", decMax, accMax))

        self._log('Sending configuration: {}'.format(config))

        self._configure(config)

    def _control(self, ctrl, value, pos_ctrl=False):
        self._pos_reached = False if pos_ctrl else None
        self._port.interface.set_motor_port_control_value(self._port.id, [ctrl] + value)

    def on_status_changed(self, cb):
        if not callable(cb):
            cb = None

        self._status_changed_callback = cb

    def _raise_status_changed_callback(self):
        if self._status_changed_callback:
            self._status_changed_callback(self._port)

    @property
    def speed(self):
        return self._speed

    @property
    def position(self):
        return self._pos

    @property
    def power(self):
        return self._power

    @property
    def is_moving(self):
        stopped = math.fabs(round(self._speed, 2)) == 0 and math.fabs(self._power) < 80
        if self._pos_reached is None:
            return not stopped
        else:
            return not (self._pos_reached and stopped)

    def set_speed(self, speed, power_limit=None):
        self._log('set_speed')
        if power_limit is None:
            control = list(struct.pack("<f", speed))
        else:
            control = list(struct.pack("<ff", speed, power_limit))

        self._control(1, control)

    def set_position(self, position: int, speed_limit=None, power_limit=None, pos_type='absolute'):
        """
        @param position: measured in degrees, depending on pos_type
        @param speed_limit: maximum speed in degrees per seconds
        @param power_limit: maximum power in percent
        @param pos_type: 'absolute': turn to this angle, counted from startup; 'relative': turn this many degrees
        """
        self._log('set_position')
        position = int(position)

        if speed_limit is not None and power_limit is not None:
            control = list(struct.pack("<lff", position, speed_limit, power_limit))
        elif speed_limit is not None:
            control = list(struct.pack("<lbf", position, 1, speed_limit))
        elif power_limit is not None:
            control = list(struct.pack("<lbf", position, 0, power_limit))
        else:
            control = list(struct.pack("<l", position))

        pos_request_types = {'absolute': 2, 'relative': 3}
        self._control(pos_request_types[pos_type], control, True)

    def set_power(self, power):
        self._log('set_power')
        power = clip(power, -100, 100)
        if power < 0:
            power = 256 + power
        self._control(0, [power])

    def update_status(self, data):
        if len(data) == 9:
            (power, pos, speed) = struct.unpack('<blf', data)
            pos_reached = None
        elif len(data) == 10:
            (power, pos, speed, pos_reached) = struct.unpack('<blfb', data)
        else:
            self._log('Received {} bytes of data instead of 9 or 10'.format(len(data)))
            return

        self._pos = pos
        self._speed = speed
        self._power = power
        self._pos_reached = pos_reached

        self._raise_status_changed_callback()

    def get_status(self):
        data = self._read()

        self.update_status(data)
        return DcMotorStatus(position=self._pos, speed=self._speed, power=self._power)

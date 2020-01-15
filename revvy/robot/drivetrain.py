# SPDX-License-Identifier: GPL-3.0-only

from revvy.mcu.rrrc_control import RevvyControl
from revvy.utils.logger import get_logger


class DrivetrainTypes:
    NONE = 0
    DIFFERENTIAL = 1


class DifferentialDrivetrain:
    NOT_ASSIGNED = 0
    LEFT = 1
    RIGHT = 2

    CONTROL_GO_POS = 0
    CONTROL_GO_SPD = 1
    CONTROL_STOP = 2

    def __init__(self, interface: RevvyControl, motor_port_count):
        self._interface = interface
        self._motor_count = motor_port_count
        self._motors = []
        self._left_motors = []
        self._right_motors = []

        self._log = get_logger('Drivetrain')

    @property
    def motors(self):
        return self._motors

    def reset(self):
        self._motors.clear()
        self._left_motors.clear()
        self._right_motors.clear()

    def add_left_motor(self, motor):
        self._log('Add motor {} to left side'.format(motor.id))
        self._motors.append(motor)
        self._left_motors.append(motor)

    def add_right_motor(self, motor):
        self._log('Add motor {} to right side'.format(motor.id))
        self._motors.append(motor)
        self._right_motors.append(motor)

    def set_speeds(self, left, right, power_limit=None):
        commands = []
        for motor in self._left_motors:
            commands.append(motor.create_set_speed_command(left, power_limit))

        for motor in self._right_motors:
            commands.append(motor.create_set_speed_command(right, power_limit))

        self._interface.set_motor_port_control_value(commands)

    def turn(self, turn_angle, wheel_speed=0, power_limit=0):
        pass

    def move(self, left, right, left_speed=None, right_speed=None, power_limit=None):
        commands = []
        for motor in self._left_motors:
            commands.append(motor.create_set_position_command(left, left_speed, power_limit))

        for motor in self._right_motors:
            commands.append(motor.create_set_position_command(right, right_speed, power_limit))

        self._interface.set_motor_port_control_value(commands)

    @property
    def is_moving(self):
        return any(motor.is_moving for motor in self._motors)

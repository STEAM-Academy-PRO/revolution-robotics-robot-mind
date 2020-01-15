# SPDX-License-Identifier: GPL-3.0-only

from revvy.mcu.rrrc_control import RevvyControl
from revvy.robot.ports.common import PortInstance
from revvy.utils.awaiter import AwaiterImpl
from revvy.utils.logger import get_logger


class DrivetrainTypes:
    NONE = 0
    DIFFERENTIAL = 1


class DifferentialDrivetrain:

    def __init__(self, interface: RevvyControl, motor_port_count):
        self._interface = interface
        self._motor_count = motor_port_count
        self._motors = []
        self._motors_moving = []
        self._left_motors = []
        self._right_motors = []

        self._log = get_logger('Drivetrain')

        self._awaiter = None
        self._update_callback = None

    def _on_motor_config_changed(self, motor, config):
        # if a motor config changes, remove the motor from the drivetrain
        idx = self._motors.index(motor)

        del self._motors[idx]
        del self._motors_moving[idx]

        try:
            self._left_motors.remove(motor)
        except ValueError:
            pass

        try:
            self._right_motors.remove(motor)
        except ValueError:
            pass

    def _on_motor_status_changed(self, motor):
        callback = self._update_callback
        if callback:
            callback(motor)

    @property
    def motors(self):
        return self._motors

    def reset(self):
        for motor in self._motors:
            motor.on_status_changed.remove(self._on_motor_status_changed)
            motor.on_config_changed.remove(self._on_motor_config_changed)

        self._motors.clear()
        self._motors_moving.clear()
        self._left_motors.clear()
        self._right_motors.clear()

    def add_left_motor(self, motor: PortInstance):
        self._log('Add motor {} to left side'.format(motor.id))
        self._motors.append(motor)
        self._motors_moving.append(False)
        self._left_motors.append(motor)

        motor.on_config_changed.add(self._on_motor_config_changed)

    def add_right_motor(self, motor: PortInstance):
        self._log('Add motor {} to right side'.format(motor.id))
        self._motors.append(motor)
        self._motors_moving.append(False)
        self._right_motors.append(motor)

        motor.on_config_changed.add(self._on_motor_config_changed)

    def stop_release(self):
        commands = []
        for motor in self._left_motors:
            commands.append(motor.create_set_power_command(0))

        for motor in self._right_motors:
            commands.append(motor.create_set_power_command(0))

        self._awaiter = None
        self._interface.set_motor_port_control_value(commands)

    def set_speeds(self, left, right, power_limit=None):
        commands = []
        for motor in self._left_motors:
            commands.append(motor.create_set_speed_command(left, power_limit))

        for motor in self._right_motors:
            commands.append(motor.create_set_speed_command(right, power_limit))

        self._awaiter = None
        self._interface.set_motor_port_control_value(commands)

    def turn(self, turn_angle, wheel_speed=0, power_limit=0):
        pass

    def _update_move(self, changed_motor):
        motor_idx = self._motors.index(changed_motor)
        self._motors_moving[motor_idx] = changed_motor.is_moving

        if not self.is_moving:
            awaiter = self._awaiter
            if self._awaiter:
                awaiter.finish()

    def move(self, left, right, left_speed=None, right_speed=None, power_limit=None):
        commands = []
        for motor in self._left_motors:
            commands.append(motor.create_relative_position_command(left, left_speed, power_limit))

        for motor in self._right_motors:
            commands.append(motor.create_relative_position_command(right, right_speed, power_limit))

        awaiter = AwaiterImpl()

        awaiter.on_cancelled(self.stop_release)
        awaiter.on_result(self.stop_release)

        self._awaiter = awaiter
        self._update_callback = self._update_move

        self._interface.set_motor_port_control_value(commands)
        self._motors_moving = [True] * len(self._motors)

        return awaiter

    @property
    def is_moving(self):
        return any(self._motors_moving)

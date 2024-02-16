from abc import ABC
import struct
from functools import partial

from revvy.robot.ports.common import PortInstance
from revvy.robot.ports.motors.base import MotorConstants, MotorStatus, MotorPortDriver
from revvy.utils.awaiter import Awaiter, Awaiter
from revvy.utils.functions import clip


class MotorCommand(ABC):
    def __init__(self, request_type):
        self.request_type = request_type

    @staticmethod
    def serialize(self) -> bytes:
        pass

    def command_to_port(self, port_idx):
        command_data = [self.request_type, *self.serialize()]

        header = ((len(command_data) << 3) & 0xF8) | port_idx

        return (header, *command_data)


class SetPowerCommand(MotorCommand):
    def __init__(self, power):
        REQUEST_POWER = 0
        super().__init__(REQUEST_POWER)

        self.power = clip(power, -100, 100)

    def serialize(self) -> bytes:
        return struct.pack("<b", self.power)


class SetSpeedCommand(MotorCommand):
    def __init__(self, speed, power_limit=None):
        REQUEST_SPEED = 1
        super().__init__(REQUEST_SPEED)

        self.speed = speed
        self.power_limit = power_limit

    def serialize(self) -> bytes:
        if self.power_limit is None:
            control = struct.pack("<f", self.speed)
        else:
            control = struct.pack("<ff", self.speed, self.power_limit)

        return control


class SetPositionCommand(MotorCommand):
    REQUEST_ABSOLUTE = 2
    REQUEST_RELATIVE = 3

    def __init__(self, request_type, position, speed_limit=None, power_limit=None):
        super().__init__(request_type)
        self.position = int(position)
        self.speed_limit = speed_limit
        self.power_limit = power_limit

    def serialize(self) -> bytes:
        LIMIT_KIND_POWER = 0
        LIMIT_KIND_SPEED = 1

        if self.speed_limit is None:
            if self.power_limit is None:
                control = struct.pack("<l", self.position)
            else:
                control = struct.pack("<lbf", self.position, LIMIT_KIND_POWER, self.power_limit)
        else:
            if self.power_limit is None:
                control = struct.pack("<lbf", self.position, LIMIT_KIND_SPEED, self.speed_limit)
            else:
                control = struct.pack("<lff", self.position, self.speed_limit, self.power_limit)

        return control


class PidConfig:
    def __init__(self, config):
        (p, i, d, lower_limit, upper_limit) = config

        self._p = p
        self._i = i
        self._d = d
        self._lower_output_limit = lower_limit
        self._upper_output_limit = upper_limit

    def serialize(self) -> bytes:
        struct.pack(
            "<5f", self._p, self._i, self._d, self._lower_output_limit, self._upper_output_limit
        )


class AccelerationLimitConfig:
    def __init__(self, config):
        (decMax, accMax) = config

        self._deceleration = decMax
        self._acceleration = accMax

    def serialize(self) -> bytes:
        struct.pack("<ff", self._deceleration, self._acceleration)


class LinearityConfig:
    def __init__(self, config):
        self._points = config

    def serialize(self) -> bytes:
        config = []
        for x, y in self._points.items():
            config += struct.pack("<ff", x, y)
        config


class DcMotorDriverConfig:
    def __init__(self, port_config):
        self._port_config = port_config
        self._position_pid = PidConfig(self._port_config["position_controller"])
        self._speed_pid = PidConfig(self._port_config["speed_controller"])
        self._acceleration_limits = AccelerationLimitConfig(port_config["acceleration_limits"])

        self._max_current = port_config["max_current"]
        self._resolution = port_config["encoder_resolution"] * port_config["gear_ratio"]

        self._linearity = LinearityConfig(port_config.get("linearity", {}))

    def serialize(self) -> bytes:
        return [
            *struct.pack("<f", self._resolution),
            *self._position_pid.serialize(),
            *self._speed_pid.serialize(),
            *self._acceleration_limits.serialize(),
            *struct.pack("<f", self._max_current),
            *self._linearity.serialize(),
        ]


class DcMotorController(MotorPortDriver):
    """Generic driver for dc motors"""

    def __init__(self, port: PortInstance[MotorPortDriver], port_config):
        super().__init__(port, "DcMotor")
        self._port = port
        self._port_config = DcMotorDriverConfig(port_config)

        self._pos = 0
        self._speed = 0
        self._power = 0
        self._pos_offset = 0

        self._awaiter = None
        self._status = MotorStatus.NORMAL

        self._timeout = 0

        # TODO: remove these in favour of "Command to ports" API. Keep in mind that drivetrain
        # sends multiple commands in one go.
        port_idx = self._port.id - 1
        self.create_set_power_command = lambda power: SetPowerCommand(power).command_to_port(
            port_idx
        )
        self.create_set_speed_command = lambda speed, power_limit=None: SetSpeedCommand(
            speed, power_limit
        ).command_to_port(port_idx)
        self.create_absolute_position_command = (
            lambda position, speed_limit=None, power_limit=None: SetPositionCommand(
                SetPositionCommand.REQUEST_ABSOLUTE, position, speed_limit, power_limit
            ).command_to_port(port_idx)
        )
        self.create_relative_position_command = (
            lambda position, speed_limit=None, power_limit=None: SetPositionCommand(
                SetPositionCommand.REQUEST_RELATIVE, position, speed_limit, power_limit
            ).command_to_port(port_idx)
        )

        port.interface.set_motor_port_config(port.id, self._port_config.serialize())

    def _cancel_awaiter(self):
        awaiter, self._awaiter = self._awaiter, None
        if awaiter:
            self.log("Cancelling previous request")
            awaiter.cancel()

    @property
    def speed(self):
        return self._speed

    @property
    def pos(self):
        return self._pos + self._pos_offset

    @pos.setter
    def pos(self, val):
        self._pos_offset = val - self._pos
        self.log(f"setting position offset to {self._pos_offset}")

    @property
    def power(self):
        return self._power

    def set_power(self, power):
        self._cancel_awaiter()
        self.log("set_power")

        self._port.interface.set_motor_port_control_value(self.create_set_power_command(power))

    def set_speed(self, speed, power_limit=None):
        self._cancel_awaiter()
        self.log("set_speed")

        self._port.interface.set_motor_port_control_value(
            self.create_set_speed_command(speed, power_limit)
        )

    def set_position(
        self, position: int, speed_limit=None, power_limit=None, pos_type="absolute"
    ) -> Awaiter:
        """
        @param position: measured in degrees, depending on pos_type
        @param speed_limit: maximum speed in degrees per seconds
        @param power_limit: maximum power in percent
        @param pos_type: 'absolute': turn to this angle, counted from startup; 'relative': turn this many degrees
        """
        self._cancel_awaiter()
        self.log("set_position")

        def _finished():
            self._awaiter = None

        def _canceled():
            self.set_power(0)

        awaiter = Awaiter()
        awaiter.on_finished(_finished)
        awaiter.on_cancelled(_canceled)

        self._awaiter = awaiter

        if pos_type == "absolute":
            position -= self._pos_offset
            command = self.create_absolute_position_command(position, speed_limit, power_limit)
        elif pos_type == "relative":
            command = self.create_relative_position_command(position, speed_limit, power_limit)
        else:
            raise ValueError(f"Invalid pos_type {pos_type}")

        self._port.interface.set_motor_port_control_value(command)

        return awaiter

    @property
    def status(self) -> MotorStatus:
        return self._status

    def _update_motor_status(self, status: MotorStatus):
        self._status = status
        awaiter = self._awaiter
        if awaiter:
            if status == MotorStatus.NORMAL:
                pass
            elif status == MotorStatus.GOAL_REACHED:
                awaiter.finish()
            elif status == MotorStatus.BLOCKED:
                awaiter.cancel()

    def update_status(self, data):
        if len(data) == 10:
            status, self._power, self._pos, self._speed = struct.unpack("<bblf", data)

            self._update_motor_status(MotorStatus(status))
            self.on_status_changed.trigger(self._port)
        else:
            self.log(f"Received {len(data)} bytes of data instead of 10")

    def stop(self, action: int = MotorConstants.ACTION_RELEASE):
        self.log("stop")
        if action == MotorConstants.ACTION_STOP_AND_HOLD:
            self.set_speed(0)
        else:
            self.set_power(0)

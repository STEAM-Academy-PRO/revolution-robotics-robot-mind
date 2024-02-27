from abc import ABC, abstractmethod
import enum
import struct
from threading import Lock
from typing import List, NamedTuple, Optional

from revvy.robot.ports.common import PortInstance
from revvy.robot.ports.motors.base import MotorConstants, MotorStatus, MotorPortDriver
from revvy.utils.awaiter import Awaiter, Awaiter
from revvy.utils.functions import clip
from revvy.utils.logger import LogLevel


class ThresholdKind(enum.IntEnum):
    DEGREES = 0
    PERCENT = 1

    def serialize(self) -> bytes:
        return struct.pack("b", self)


class PositionThreshold(NamedTuple):
    kind: ThresholdKind
    value: float

    @staticmethod
    def degrees(degrees: float):
        return PositionThreshold(kind=ThresholdKind.DEGREES, value=degrees)

    @staticmethod
    def percent(percent: float):
        return PositionThreshold(kind=ThresholdKind.PERCENT, value=percent / 100.0)

    def serialize(self) -> bytes:
        """
        >>> list(PositionThreshold(ThresholdKind.DEGREES, 5).serialize())
        [0, 0, 0, 160, 64]
        >>> list(PositionThreshold(ThresholdKind.PERCENT, 0.5).serialize())
        [1, 0, 0, 0, 63]
        """

        return bytes([*self.kind.serialize(), *struct.pack("<f", self.value)])


class MotorCommand(ABC):
    def __init__(self, request_type):
        self.request_type = request_type

    @abstractmethod
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


class PidConfig(NamedTuple):
    p: float
    i: float
    d: float
    lower_output_limit: float
    upper_output_limit: float

    def serialize(self) -> bytes:
        return struct.pack(
            "<5f", self.p, self.i, self.d, self.lower_output_limit, self.upper_output_limit
        )


class TwoValuePidConfig(NamedTuple):
    slow: PidConfig
    fast: PidConfig
    fast_threshold: PositionThreshold

    def serialize(self) -> bytes:
        return bytes(
            [*self.slow.serialize(), *self.fast.serialize(), *self.fast_threshold.serialize()]
        )


class AccelerationLimitConfig:
    def __init__(self, config: tuple[float, float]):
        (decMax, accMax) = config

        self._deceleration = decMax
        self._acceleration = accMax

    def serialize(self) -> bytes:
        return struct.pack("<ff", self._deceleration, self._acceleration)


class LinearityConfig:
    def __init__(self, config: List[tuple[float, int]]):
        self._points = config

    def serialize(self) -> bytes:
        config = []
        for x, y in self._points:
            config += struct.pack("<ff", x, y)
        return bytes(config)


class DcMotorDriverConfig:
    # TODO: we should do better than 'dict'
    def __init__(self, port_config: dict):
        self._port_config = port_config
        self._position_pid = self._port_config["position_controller"]
        self._speed_pid = self._port_config["speed_controller"]
        self._acceleration_limits = AccelerationLimitConfig(port_config["acceleration_limits"])

        self._max_current = port_config["max_current"]
        self._resolution = port_config["encoder_resolution"] * port_config["gear_ratio"]

        self._linearity = LinearityConfig(port_config.get("linearity", []))

    def serialize(self) -> bytes:
        return bytes(
            [
                *struct.pack("<f", self._resolution),
                *self._position_pid.serialize(),
                *self._speed_pid.serialize(),
                *self._acceleration_limits.serialize(),
                *struct.pack("<f", self._max_current),
                *self._linearity.serialize(),
            ]
        )


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
        self._current_position_request: Optional[int] = None
        self._lock = Lock()
        port.interface.set_motor_port_config(port.id, self._port_config.serialize())

    # TODO: explain the arguments' units
    # TODO: remove these in favour of "Command to ports" API? Keep in mind that drivetrain
    # sends multiple commands in one go.
    def create_set_power_command(self, power) -> bytes:
        """Create a command to set the motor power of the current motor.

        You can send the returned command (or multiple commands)
        using `interface.set_motor_port_control_value`
        """
        return SetPowerCommand(power).command_to_port(self._port.id - 1)

    def create_set_speed_command(self, speed, power_limit=None) -> bytes:
        """Create a command to set the regulated speed of the current motor.

        You can send the returned command (or multiple commands)
        using `interface.set_motor_port_control_value`
        """
        return SetSpeedCommand(speed, power_limit).command_to_port(self._port.id - 1)

    def create_absolute_position_command(
        self, position, speed_limit=None, power_limit=None
    ) -> bytes:
        """Create a command to set the regulated position of the current motor.

        The position is measured in degrees, counted from when the port is configured.

        You can send the returned command (or multiple commands)
        using `interface.set_motor_port_control_value`
        """
        return SetPositionCommand(
            SetPositionCommand.REQUEST_ABSOLUTE, position, speed_limit, power_limit
        ).command_to_port(self._port.id - 1)

    def create_relative_position_command(
        self, position, speed_limit=None, power_limit=None
    ) -> bytes:
        """Create a command to turn the current motor. The turning angle is relative to the current position.

        You can send the returned command (or multiple commands)
        using `interface.set_motor_port_control_value`
        """
        return SetPositionCommand(
            SetPositionCommand.REQUEST_RELATIVE, position, speed_limit, power_limit
        ).command_to_port(self._port.id - 1)

    def _cancel_awaiter(self) -> None:
        awaiter, self._awaiter = self._awaiter, None
        self._current_position_request = None
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

    def set_power(self, power) -> None:
        self._cancel_awaiter()
        self.log("set_power")

        self._port.interface.set_motor_port_control_value(self.create_set_power_command(power))

    def set_speed(self, speed, power_limit=None) -> None:
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

        def _finished() -> None:
            self._awaiter = None

        def _canceled() -> None:
            self.set_power(0)

        awaiter = Awaiter()
        awaiter.on_finished(_finished)
        awaiter.on_cancelled(_canceled)

        if pos_type == "absolute":
            position -= self._pos_offset
            command = self.create_absolute_position_command(position, speed_limit, power_limit)
        elif pos_type == "relative":
            command = self.create_relative_position_command(position, speed_limit, power_limit)
        else:
            raise ValueError(f"Invalid pos_type {pos_type}")

        with self._lock:
            self._awaiter = awaiter
            response = self._port.interface.set_motor_port_control_value(command)
            self._current_position_request = response[0]
        self.log(f"set_position request id: {self._current_position_request}")

        return awaiter

    @property
    def status(self) -> MotorStatus:
        return self._status

    def _update_motor_status(self, status: MotorStatus, request_id: int):
        with self._lock:
            self._status = status
            awaiter = self._awaiter
            if awaiter:
                if self._current_position_request is not None:
                    if request_id != self._current_position_request:
                        self.log(f"unexpected request id: {request_id}", LogLevel.DEBUG)
                        return

                if status == MotorStatus.NORMAL:
                    return
                elif status == MotorStatus.GOAL_REACHED:
                    self.log(f"goal reached: {request_id}", LogLevel.DEBUG)
                    awaiter.finish()
                elif status == MotorStatus.BLOCKED:
                    self.log(f"blocked: {request_id}", LogLevel.DEBUG)
                    awaiter.cancel()

    def update_status(self, data) -> None:
        if len(data) == 11:
            raw_status = struct.unpack("<bblfB", data)
            status, self._power, self._pos, self._speed, current_task = raw_status

            self._update_motor_status(MotorStatus(status), current_task)
            self.on_status_changed.trigger(self._port)
        else:
            self.log(f"Received {len(data)} bytes of data instead of 10")

    def stop(self, action: int = MotorConstants.ACTION_RELEASE):
        self.log("stop")
        if action == MotorConstants.ACTION_STOP_AND_HOLD:
            self.set_speed(0)
        else:
            self.set_power(0)

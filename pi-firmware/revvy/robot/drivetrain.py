from abc import ABC, abstractmethod
import itertools
from contextlib import suppress
from threading import Lock, Timer
from typing import Optional

from revvy.mcu.rrrc_control import RevvyControl
from revvy.robot.imu import IMU
from revvy.robot.ports.common import PortInstance
from revvy.robot.ports.motors.base import MotorPortDriver, MotorStatus, MotorConstants
from revvy.utils.awaiter import Awaiter, AwaiterState
from revvy.utils.functions import clip
from revvy.utils.logger import get_logger
from revvy.utils.stopwatch import Stopwatch


class DrivetrainController(ABC):
    def __init__(self, drivetrain: "DifferentialDrivetrain"):
        self._drivetrain = drivetrain
        self._awaiter = Awaiter()
        self._awaiter.on_cancelled(self._drivetrain._apply_release)
        self._awaiter.on_finished(self._drivetrain._apply_release)

        # If there are no motors configured to the drive train, avoid trying to control them
        # Otherwise we might wait forever for a status update to arrive
        if len(self._drivetrain.motors) == 0:
            self._awaiter.finish()
            return

    @property
    def awaiter(self) -> Awaiter:
        return self._awaiter

    @abstractmethod
    def update(self) -> None:
        pass


class TimeController(DrivetrainController):

    def __init__(self, drivetrain: "DifferentialDrivetrain", timeout):
        super().__init__(drivetrain)

        t = Timer(timeout, self._awaiter.finish)
        self._awaiter.on_cancelled(t.cancel)
        t.start()

    def update(self) -> None:
        pass


class TurnController(DrivetrainController):
    Kp = 0.75

    def __init__(
        self,
        drivetrain: "DifferentialDrivetrain",
        turn_angle: int,
        wheel_speed: int,
        power_limit: int,
    ):
        self._max_turn_wheel_speed = wheel_speed
        self._max_turn_power = power_limit

        self._turn_angle = turn_angle
        self._start_angle = drivetrain.yaw
        self._last_yaw_change_time = Stopwatch()

        # We store the last yaw angle and use it to detect if the robot is stuck.
        # If the yaw angle does not change for 3 seconds, we cancel the controller.
        # We're sensitive to changes larger than 0.5 degrees to avoid false positives due to noise.
        # This value starts from `None` which causes the controller to drive the motors on the first
        # update. This is a bit of a hack, but we need the motors to turn in order for `update` to
        # be called again.
        self._last_yaw_angle = None

        super().__init__(drivetrain)

    def update(self) -> None:
        yaw = self._drivetrain.yaw
        error = abs(self._turn_angle) - abs(self._start_angle - yaw)
        abs_error = abs(error)
        direction = 1 if self._turn_angle > 0 else -1

        if abs_error < 1 or abs_error > 2 * abs(self._turn_angle):
            # goal reached or someone picked up the robot and started turning it by hand in the wrong direction?
            self._drivetrain._log("Turn controller finished")
            self._awaiter.finish()

        elif self._last_yaw_angle is None or abs(self._last_yaw_angle - yaw) > 0.5:
            self._last_yaw_angle = yaw
            self._last_yaw_change_time.reset()

            # try Kp=10 and saturate on max allowed wheel speed?

            # update motor speeds using a P regulator
            p = clip(
                direction * error * self.Kp, -self._max_turn_wheel_speed, self._max_turn_wheel_speed
            )
            self._drivetrain._apply_speeds(-p, p, self._max_turn_power)

        elif self._last_yaw_change_time.elapsed > 3:
            # yaw angle has not changed for 3 seconds
            self._drivetrain._log("Turn controller blocked, stopping")
            self._awaiter.cancel()


class MoveController(DrivetrainController):
    def __init__(
        self,
        drivetrain: "DifferentialDrivetrain",
        left,
        right,
        left_speed=None,
        right_speed=None,
        power_limit=None,
    ):
        drivetrain._apply_positions(left, right, left_speed, right_speed, power_limit)

        super().__init__(drivetrain)

    def update(self) -> None:
        # stop if all is blocked or done
        if all(m.driver.status != MotorStatus.NORMAL for m in self._drivetrain.motors):
            self._drivetrain._log("Move controller finished")
            self._awaiter.finish()


class DifferentialDrivetrain:
    max_rpm = 120

    def __init__(self, interface: RevvyControl, imu: IMU):
        self._interface = interface
        self._motors: list[PortInstance[MotorPortDriver]] = []
        self._left_motors: list[PortInstance[MotorPortDriver]] = []
        self._right_motors: list[PortInstance[MotorPortDriver]] = []

        self._log = get_logger("Drivetrain")
        self._imu = imu
        self._controller: Optional[DrivetrainController] = None
        self.request_ids = []
        self._update_lock = Lock()
        self._command_lock = Lock()

    @property
    def yaw(self) -> float:
        return self._imu.yaw_angle

    @property
    def motors(self) -> list[PortInstance[MotorPortDriver]]:
        return self._motors

    @property
    def left_motors(self) -> list[PortInstance[MotorPortDriver]]:
        return self._left_motors

    @property
    def right_motors(self) -> list[PortInstance[MotorPortDriver]]:
        return self._right_motors

    def _abort_controller(self) -> None:
        controller, self._controller = self._controller, None
        if controller:
            controller.awaiter.cancel()

    def reset(self) -> None:
        self._log("reset")
        self._abort_controller()

        for motor in self._motors:
            motor.driver.on_status_changed.remove(self._on_motor_status_changed)
            motor.on_config_changed.remove(self._on_motor_config_changed)

        self._motors.clear()
        self._left_motors.clear()
        self._right_motors.clear()
        self.request_ids.clear()

    def _add_motor(self, motor: PortInstance[MotorPortDriver]):
        self._motors.append(motor)

        motor.driver.on_status_changed.add(self._on_motor_status_changed)
        motor.on_config_changed.add(self._on_motor_config_changed)

        self.request_ids.append(0)

    def add_left_motor(self, motor: PortInstance[MotorPortDriver]):
        self._log(f"Add motor {motor.id} to left side")
        self._left_motors.append(motor)
        self._add_motor(motor)

    def add_right_motor(self, motor: PortInstance[MotorPortDriver]):
        self._log(f"Add motor {motor.id} to right side")
        self._right_motors.append(motor)
        self._add_motor(motor)

    def _on_motor_config_changed(self, motor: PortInstance[MotorPortDriver], _):
        # if a motor config changes, remove the motor from the drivetrain
        self._motors.remove(motor)
        self.request_ids.pop()

        with suppress(ValueError):
            self._left_motors.remove(motor)

        with suppress(ValueError):
            self._right_motors.remove(motor)

    def _on_motor_status_changed(self, _: tuple[PortInstance[MotorPortDriver], int]) -> None:
        # We're sending commands on two threads: the main thread and the status update thread.
        # We must prevent the status update thread from stopping a command prematurely.
        with self._command_lock:
            with self._update_lock:
                # only react to updates to our own requests
                if any(
                    self._motors[idx].driver.active_request_id != self.request_ids[idx]
                    for idx in range(len(self._motors))
                ):
                    # only start reacting to changes once all motors report status to the newest request
                    return
            if all(m.driver.status == MotorStatus.BLOCKED for m in self._motors):
                self._log("All motors blocked, releasing")
                self._abort_controller()
            else:
                controller = self._controller
                if controller:
                    controller.update()

    def _apply_motor_commands(self, commands: bytes):
        with self._update_lock:
            self.request_ids = list(self._interface.set_motor_port_control_value(commands))

    def _apply_release(self):
        # this runs as a callback to Awaiter.finish() or cancel(), in both
        # cases controller should be cleaned up, else _on_motor_status_changed
        # will continue to use controller.update, see above, making the program
        # leave long after it is actually finished
        self._controller = None
        commands = itertools.chain(
            *(motor.driver.create_set_power_command(0) for motor in self._left_motors),
            *(motor.driver.create_set_power_command(0) for motor in self._right_motors),
        )
        self._apply_motor_commands(bytes(commands))

    def _apply_speeds(self, left: float, right: float, power_limit: Optional[float]):
        commands = itertools.chain(
            *(
                motor.driver.create_set_speed_command(  # pyright: ignore (Don't know about DcMotor driver here)
                    left, power_limit
                )
                for motor in self._left_motors
            ),
            *(
                motor.driver.create_set_speed_command(  # pyright: ignore (Don't know about DcMotor driver here)
                    right, power_limit
                )
                for motor in self._right_motors
            ),
        )
        self._apply_motor_commands(bytes(commands))

    def _apply_positions(self, left, right, left_speed, right_speed, power_limit):
        commands = itertools.chain(
            *(
                motor.driver.create_relative_position_command(left, left_speed, power_limit)
                for motor in self._left_motors
            ),
            *(
                motor.driver.create_relative_position_command(right, right_speed, power_limit)
                for motor in self._right_motors
            ),
        )
        self._apply_motor_commands(bytes(commands))

    def _process_unit_speed(self, speed, unit_speed):
        if unit_speed == MotorConstants.UNIT_SPEED_RPM:
            power = None
        elif unit_speed == MotorConstants.UNIT_SPEED_PWR:
            power, speed = speed, self.max_rpm
        else:
            raise ValueError(f"Invalid unit_speed: {unit_speed}")

        return power, speed

    def stop_release(self):
        with self._command_lock:
            self._log("stop and release")
            self._abort_controller()

            self._apply_release()

    def set_speeds(self, left, right, power_limit=None):
        with self._command_lock:
            self._log(f"set speeds: {left} {right} {power_limit}")
            self._abort_controller()

            self._apply_speeds(left, right, power_limit)

    def set_speed(self, direction, speed, unit_speed=MotorConstants.UNIT_SPEED_RPM):
        self._log(f"set speed: {direction} {speed} {unit_speed}")
        self._abort_controller()
        multipliers = {
            MotorConstants.DIRECTION_FWD: 1,
            MotorConstants.DIRECTION_BACK: -1,
        }

        power, speed = self._process_unit_speed(speed, unit_speed)

        left_speed = right_speed = multipliers[direction] * speed
        self._apply_speeds(left_speed, right_speed, power)

    def drive(self, direction, rotation, unit_rotation, speed, unit_speed) -> Awaiter:
        with self._command_lock:
            self._log(f"drive: {direction} {rotation} {unit_rotation} {speed} {unit_speed}")
            self._abort_controller()

            multipliers = {
                MotorConstants.DIRECTION_FWD: 1,
                MotorConstants.DIRECTION_BACK: -1,
            }

            power, speed = self._process_unit_speed(speed, unit_speed)

            if unit_rotation == MotorConstants.UNIT_SEC:
                left_speed = right_speed = speed * multipliers[direction]
                self._apply_speeds(left_speed, right_speed, power_limit=power)

                self._controller = TimeController(self, timeout=rotation)

            elif unit_rotation == MotorConstants.UNIT_ROT:
                left = right = 360 * rotation * multipliers[direction]
                left_speed = right_speed = speed

                self._controller = MoveController(self, left, right, left_speed, right_speed, power)
            else:
                raise ValueError(f"Invalid unit_rotation: {unit_rotation}")

            return self._controller.awaiter

    def turn(self, direction, rotation, unit_rotation, speed, unit_speed) -> Awaiter:
        with self._command_lock:
            self._log(f"turn: {direction} {rotation} {unit_rotation} {speed} {unit_speed}")
            self._abort_controller()

            multipliers = {
                MotorConstants.DIRECTION_LEFT: 1,  # +ve number -> CCW turn
                MotorConstants.DIRECTION_RIGHT: -1,  # -ve number -> CW turn
            }

            power, speed = self._process_unit_speed(speed, unit_speed)

            if unit_rotation == MotorConstants.UNIT_SEC:

                right_speed = speed * multipliers[direction]
                self._apply_speeds(-1 * right_speed, right_speed, power_limit=power)

                self._controller = TimeController(self, timeout=rotation)

            elif unit_rotation == MotorConstants.UNIT_TURN_ANGLE:

                self._controller = TurnController(
                    self,
                    turn_angle=rotation * multipliers[direction],
                    wheel_speed=speed,
                    power_limit=power,
                )

                # We need to call update() because we only get notified about changes
                # and update starts the movement.
                self._controller.update()

                # NOTE: update() may immediately complete the turn. This can call _apply_release()
                # which immediately sets _controller to None.
            else:
                raise ValueError(f"Invalid unit_rotation: {unit_rotation}")

            if self._controller is not None:
                awaiter = self._controller.awaiter
            else:
                awaiter = Awaiter(AwaiterState.FINISHED)

            return awaiter

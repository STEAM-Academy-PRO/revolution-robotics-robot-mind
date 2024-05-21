"""
This is the robot's Blockly API.
Whatever code blockly generates, it compiles to python
code that uses these functions.
"""

from abc import ABC
from math import floor
import time
import random

from functools import partial
from enum import Enum

from typing import (
    TYPE_CHECKING,
    Callable,
    Generic,
    Iterator,
    NamedTuple,
    Optional,
    TypeVar,
    Union,
)

from revvy.robot.imu import IMU
from revvy.robot.ports.sensors.simple import ColorSensorReading

# # To have types, use this to avoid circular dependencies.
if TYPE_CHECKING:
    from revvy.robot.robot import Robot
    from revvy.scripting.runtime import ScriptHandle
    from revvy.robot_config import RobotConfig
    from revvy.robot.drivetrain import DifferentialDrivetrain


from revvy.robot.led_ring import RingLed
from revvy.robot.ports.motors.base import MotorConstants, MotorPortDriver, MotorPositionKind
from revvy.robot.ports.sensors.base import SensorPortDriver
from revvy.robot.sound import Sound
from revvy.scripting.resource import BaseHandle, null_handle, Resource
from revvy.scripting.color_functions import (
    ColorData,
    rgb_to_hsv_gray,
    detect_line_background_colors,
    ColorDataUndefined,
    color_name_to_rgb,
)

from revvy.utils.awaiter import Awaiter
from revvy.utils.functions import hex2rgb
from revvy.robot.ports.common import PortInstance
from revvy.utils.functions import map_values
from revvy.utils.logger import get_logger


log = get_logger("RobotInterface")


class RGBChannelSensor(Enum):
    FRONT = 0
    LEFT = 1
    RIGHT = 2
    REAR = 3
    UNDEFINED = 4


class UserScriptRGBChannel(Enum):
    FRONT = 1
    RIGHT = 2
    LEFT = 3
    REAR = 4


def user_to_sensor_channel(user_channel: UserScriptRGBChannel) -> RGBChannelSensor:
    mapping = [
        (UserScriptRGBChannel.FRONT, RGBChannelSensor.FRONT),
        (UserScriptRGBChannel.LEFT, RGBChannelSensor.LEFT),
        (UserScriptRGBChannel.RIGHT, RGBChannelSensor.RIGHT),
        (UserScriptRGBChannel.REAR, RGBChannelSensor.REAR),
    ]
    for user, sensor in mapping:
        if user_channel == user.value:
            return sensor

    log(f"user_to_sensor_channel: {user_channel}")
    return RGBChannelSensor.UNDEFINED


class Wrapper(ABC):
    """Binds a shared resource (e.g. a motor port) to a script and provides a way to use it.

    Inside a resource wrapper, we may need to access the scripting environment. This base class
    provides this access, while also taking script priorities into account."""

    # FIXME: resource priority semantics are unclear, surprising and not very well usable.

    def __init__(self, script: "ScriptHandle", resource: Resource):
        self._resource = resource
        self._script = script
        self._current_handle: BaseHandle = null_handle

    def try_take_resource(self, on_interrupted: Optional[Callable[[], None]] = None) -> BaseHandle:
        """
        Intended to be used in a with statement to automatically release the resource.
        If the resource is not available, returns NullHandle which evaluates to False.
        """
        if self._script.is_stop_requested:
            self._script.log("Trying to take resource but script is stopping")
            raise InterruptedError

        if self._current_handle:
            return self._current_handle

        handle = self._resource.request(self._script.priority, on_interrupted)
        if handle:

            def _release_handle() -> None:
                self._current_handle = null_handle

            # lints ignored because pyright doesn't understand that if handle is true,
            # it's not a null_handle
            handle.on_interrupted.add(_release_handle)  # pyright: ignore
            handle.on_released.add(_release_handle)  # pyright: ignore

            self._current_handle = handle

        return self._current_handle

    def using_resource(self, callback) -> None:
        self.if_resource_available(lambda res: res.run_uninterruptable(callback))

    def if_resource_available(self, callback) -> None:
        with self.try_take_resource() as resource:
            if resource:
                callback(resource)

    def force_release_resource(self) -> None:
        handle = self._current_handle
        if handle:
            handle.interrupt()


class SensorPortWrapper(Wrapper):
    """Wrapper class to expose sensor ports to user scripts"""

    def __init__(
        self,
        script: "ScriptHandle",
        sensor: PortInstance[SensorPortDriver],
        resource: Resource,
    ):
        super().__init__(script, resource)
        self._sensor = sensor

    def read(self):
        """Return the last converted value"""
        if self._script.is_stop_requested:
            raise InterruptedError

        while not self._sensor.driver.has_data:
            self._script.sleep(0.1)

        return self._sensor.driver.value


def color_string_to_rgb(color_string: str) -> Optional[int]:
    """Interface can accept colot_string in several formats
    this can be a hex value like #or actual color name like 'red' or 'black'"""

    result = color_name_to_rgb(color_string)
    if result is not None:
        return result

    if color_string.startswith("#"):
        return hex2rgb(color_string)

    # TODO: throw an exception?
    log(f"Color string format not recognised: {color_string}")
    return None


class RingLedWrapper(Wrapper):
    """Wrapper class to expose LED ring to user scripts"""

    def __init__(self, script: "ScriptHandle", ring_led: RingLed, resource: Resource):
        super().__init__(script, resource)
        self._ring_led = ring_led
        self._user_leds = [0] * ring_led.count

    @property
    def scenario(self) -> int:
        return self._ring_led.scenario

    def start_animation(self, scenario: int):
        self.using_resource(partial(self._ring_led.start_animation, scenario))

    def set(self, leds: list[int], color):
        rgb = color_string_to_rgb(color) or 0

        for idx in leds:
            index = floor(idx - 1) % len(self._user_leds)
            self._user_leds[index] = rgb

        self.using_resource(partial(self._ring_led.display_user_frame, self._user_leds))


class MotorPortWrapper(Wrapper):
    """Wrapper class to expose motor ports to user scripts"""

    max_rpm = 150
    timeout = 5

    def __init__(
        self,
        script: "ScriptHandle",
        motor: PortInstance[MotorPortDriver],
        resource: Resource,
    ):
        super().__init__(script, resource)
        self._log = get_logger(["MotorPortWrapper", f"{motor.id}"], base=script.log)
        self._motor = motor
        self._pos_offset = 0

    @property
    def pos(self) -> int:
        return self._motor.driver.pos + self._pos_offset

    @pos.setter
    def pos(self, val: int):
        self._pos_offset = val - self._motor.driver.pos
        self._log(f"setting position offset to {self._pos_offset}")

    @pos.setter
    def pos(self, val):
        self._motor.pos = val

    def move(self, direction, amount, unit_amount, limit, unit_limit) -> None:
        self._log("move")

        # convert complete rotations to degrees
        if unit_amount == MotorConstants.UNIT_ROT:
            unit_amount = MotorConstants.UNIT_DEG
            amount *= 360

        move_motor_command_map = {
            MotorConstants.UNIT_DEG: {
                MotorConstants.UNIT_SPEED_RPM: {
                    MotorConstants.DIRECTION_FWD: lambda: self._motor.driver.set_position(
                        amount, speed_limit=limit, pos_type=MotorPositionKind.RELATIVE
                    ),
                    MotorConstants.DIRECTION_BACK: lambda: self._motor.driver.set_position(
                        -amount, speed_limit=limit, pos_type=MotorPositionKind.RELATIVE
                    ),
                },
                MotorConstants.UNIT_SPEED_PWR: {
                    MotorConstants.DIRECTION_FWD: lambda: self._motor.driver.set_position(
                        amount, power_limit=limit, pos_type=MotorPositionKind.RELATIVE
                    ),
                    MotorConstants.DIRECTION_BACK: lambda: self._motor.driver.set_position(
                        -amount, power_limit=limit, pos_type=MotorPositionKind.RELATIVE
                    ),
                },
            },
            MotorConstants.UNIT_SEC: {
                MotorConstants.UNIT_SPEED_RPM: {
                    MotorConstants.DIRECTION_FWD: lambda: self._motor.driver.set_speed(limit),
                    MotorConstants.DIRECTION_BACK: lambda: self._motor.driver.set_speed(-limit),
                },
                MotorConstants.UNIT_SPEED_PWR: {
                    MotorConstants.DIRECTION_FWD: lambda: self._motor.driver.set_power(limit),
                    MotorConstants.DIRECTION_BACK: lambda: self._motor.driver.set_power(-limit),
                },
            },
        }

        motor_control_command = move_motor_command_map[unit_amount][unit_limit][direction]

        awaiter = None

        def _interrupted() -> None:
            self._log("Movement interrupted")
            # When interrupted, always switch the motor power off before cancel,
            # so that it also stops if the unit is time.
            self._motor.driver.set_power(0)
            if awaiter:
                awaiter.cancel()

        with self.try_take_resource(_interrupted) as resource:
            if resource:
                self._log("start movement")
                awaiter = resource.run_uninterruptable(motor_control_command)

                if unit_amount == MotorConstants.UNIT_DEG:
                    # wait for movement to finish
                    if awaiter:  # can be None if resource is interrupted by another script
                        awaiter.wait()

                elif unit_amount == MotorConstants.UNIT_SEC:
                    # When moving unit is time, we set the motor to rotate "indefinitely"
                    # as we did not implement that on the motor driver level.
                    # This means, the resource.run_uninterruptable will not return
                    # an awaiter, which means it would not be stopped when cancelled,
                    # it has to be done manually.
                    try:
                        self._script.sleep(amount)
                        # Stop it after timeout.
                    finally:
                        # FIXME: while this finally solves the problem of the unstoppable
                        # block, the exact mechanism of the bug is unknown. For some reason,
                        # the script's "stop requested" callbacks either aren't called, or
                        # they don't contain the function that would stop the motor.
                        resource.run_uninterruptable(partial(self._motor.driver.set_power, 0))
                self._log("movement finished")

    def spin(self, direction: int, rotation: int, unit_rotation: int):
        # start moving depending on limits
        self._log("spin")
        set_speed_fns = {
            MotorConstants.UNIT_SPEED_RPM: {
                MotorConstants.DIRECTION_FWD: lambda: self._motor.driver.set_speed(rotation),
                MotorConstants.DIRECTION_BACK: lambda: self._motor.driver.set_speed(-rotation),
            },
            MotorConstants.UNIT_SPEED_PWR: {
                MotorConstants.DIRECTION_FWD: lambda: self._motor.driver.set_power(rotation),
                MotorConstants.DIRECTION_BACK: lambda: self._motor.driver.set_power(-rotation),
            },
        }

        self.using_resource(set_speed_fns[unit_rotation][direction])

    def stop(self, action: int):
        self.using_resource(partial(self._motor.driver.stop, action))


def wrap_async_method(owner: Wrapper, method):
    def _wrapper(*args, **kwargs) -> None:
        awaiter: Optional[Awaiter] = None

        def _interrupted() -> None:
            """Cancels the awaiter if someone with higher priority takes over the resource."""
            if awaiter:
                awaiter.cancel()

        with owner.try_take_resource(_interrupted) as resource:
            if resource:
                awaiter = method(*args, **kwargs)
                if awaiter:
                    awaiter.wait()

    return _wrapper


def wrap_sync_method(owner: Wrapper, method):
    def _wrapper(*args, **kwargs) -> None:
        with owner.try_take_resource() as resource:
            if resource:
                method(*args, **kwargs)

    return _wrapper


class DriveTrainWrapper(Wrapper):
    def __init__(
        self, script: "ScriptHandle", drivetrain: "DifferentialDrivetrain", resource: Resource
    ):
        super().__init__(script, resource)
        self.__drivetrain = drivetrain
        self.turn = wrap_async_method(self, self.__drivetrain.turn)
        self.drive = wrap_async_method(self, self.__drivetrain.drive)

    def __log(self, message: str):
        self._script.log("DriveTrain: " + message)

    def set_speed(self, direction, speed, unit_speed=MotorConstants.UNIT_SPEED_RPM) -> None:
        # self.__log("set_speed")

        resource = self.try_take_resource()
        if not resource:
            self.__log("Drivetrain: failed to get resource")
            raise Exception()
        if resource:
            try:
                self.__drivetrain.set_speed(direction, speed, unit_speed)
            finally:
                if speed == 0:
                    resource.release()

    def set_speeds(self, sl, sr) -> None:
        resource = self.try_take_resource()
        if resource:
            try:
                self.__drivetrain.set_speeds(sl, sr)
            finally:
                if sl == sr == 0:
                    resource.release()


class SoundWrapper(Wrapper):
    def __init__(self, script: "ScriptHandle", sound: Sound, resource: Resource):
        super().__init__(script, resource)
        self._sound = sound

        self.set_volume = sound.set_volume
        self._is_playing = False

    def _sound_finished(self) -> None:
        # this runs on a different thread independent of the script
        self._is_playing = False

    def _play(self, name: str):
        if not self._is_playing:
            self._is_playing = True  # one sound per thread at the same time
            self._sound.play_tune(name, self._sound_finished)

    def play_tune(self, name: str):
        # immediately releases resource after starting the playback
        self.if_resource_available(lambda _: self._play(name))


class RelativeToLineState(NamedTuple):
    front: int
    rear: int
    left: int
    right: int


on_line = RelativeToLineState(1, 1, 0, 0)
on_line_end_soon = RelativeToLineState(0, 1, 0, 0)
on_line_near_left = RelativeToLineState(1, 1, 0, 1)
on_line_near_right = RelativeToLineState(1, 1, 1, 0)
on_line_too_wide = RelativeToLineState(1, 1, 1, 1)
on_line_hole = RelativeToLineState(1, 0, 1, 1)
on_line_perpendicular = RelativeToLineState(0, 1, 1, 1)
on_line_rear_left = RelativeToLineState(0, 1, 1, 0)
on_line_rear_right = RelativeToLineState(0, 1, 0, 1)
off_line = RelativeToLineState(0, 0, 0, 0)
off_line_near_front = RelativeToLineState(1, 0, 0, 0)
off_line_near_front_left = RelativeToLineState(1, 0, 1, 0)
off_line_near_front_right = RelativeToLineState(1, 0, 0, 1)
off_line_near_left = RelativeToLineState(0, 0, 1, 0)
off_line_near_right = RelativeToLineState(0, 0, 0, 1)
off_line_left_right = RelativeToLineState(0, 0, 1, 1)


class LineDriver:
    FOLLOW_LINE_RESULT_CONTINUE = 0
    FOLLOW_LINE_RESULT_LOST = 1
    FOLLOW_LINE_RESULT_FINISH = 2
    SEARCH_LINE_FORWARD_MOTION = 0
    SEARCH_LINE_ROTATE_90 = 1

    def __init__(
        self, drivetrain: "DriveTrainWrapper", color_reader: "RobotWrapper", line_color: str
    ) -> None:
        self.__drivetrain = drivetrain
        self.__color_reader = color_reader
        self.__line_color = line_color
        self.__search_line_motion_time = 0
        self.__search_line_state_duration = 0
        self.__next_motion_duration = 0
        self.__prev_current = None
        self.__do_debug_stops = False
        self.__base_speed = 20
        self.__straight_speed_mult = 1.5
        self.__log = get_logger("LineDriver")

    def read_rgb(self, channel: RGBChannelSensor) -> str:
        sensors = self.__color_reader.read_rgb_sensor_data()
        return sensors[channel.value].name

    @property
    def __rgb_front(self) -> str:
        return self.read_rgb(RGBChannelSensor.FRONT)

    @property
    def __rgb_left(self) -> str:
        return self.read_rgb(RGBChannelSensor.LEFT)

    @property
    def __rgb_right(self) -> str:
        return self.read_rgb(RGBChannelSensor.RIGHT)

    @property
    def __rgb_rear(self) -> str:
        return self.read_rgb(RGBChannelSensor.REAR)

    def __go_inclined_forward(self, inclination) -> None:
        self.__log("INCLINED_FORWARD")
        speed_left = speed_right = self.__base_speed * self.__straight_speed_mult
        if inclination < 0:
            speed_left -= self.__base_speed * (-inclination)
        else:
            speed_right -= self.__base_speed * inclination
        self.__drivetrain.set_speeds(speed_left, speed_right)

    def __turn_left(self) -> None:
        self.__log("TURN_LEFT")
        self.__drivetrain.set_speeds(self.__base_speed * -0.25, self.__base_speed)

    def __turn_right(self) -> None:
        self.__log("TURN_RIGHT")
        self.__drivetrain.set_speeds(self.__base_speed, self.__base_speed * -0.25)

    def __go_straight(self) -> None:
        self.__log("GO_STRAIGHT")
        speed = self.__base_speed * self.__straight_speed_mult
        self.__drivetrain.set_speeds(speed, speed)

    def __stop(self) -> None:
        self.__log("STOP")
        self.__drivetrain.set_speeds(0, 0)

    def stop(self) -> None:
        self.__stop()

    def search_line_start(self) -> None:
        self.__log("search_line_start")
        self.__state = LineDriver.SEARCH_LINE_ROTATE_90
        self.__search_line_motion_time = 0
        self.__search_line_state_duration = 1

    # Returns True if line is found,
    # False is line is not found
    def search_line_update(self) -> bool:
        front_match = self.__rgb_front == self.__line_color
        rear_match = self.__rgb_rear == self.__line_color
        left_match = self.__rgb_left == self.__line_color
        right_match = self.__rgb_right == self.__line_color
        if front_match or rear_match or left_match or right_match:
            self.__log("search:line_reached")
            self.__stop()
            return True

        self.__search_line_motion_time += 1
        if self.__search_line_motion_time < self.__search_line_state_duration:
            to_go = self.__search_line_state_duration - self.__search_line_motion_time
            self.__log(f"search:state_timeout:{to_go}")
            return False

        self.__search_line_motion_time = 0
        self.__next_motion_duration += 10
        if self.__state == LineDriver.SEARCH_LINE_FORWARD_MOTION:
            self.__log("search::rotate 90")
            self.__search_line_state_duration = 15
            self.__state = LineDriver.SEARCH_LINE_ROTATE_90
            self.__turn_left()
        elif self.__state == LineDriver.SEARCH_LINE_ROTATE_90:
            self.__log("search:inclined forward")
            self.__search_line_state_duration = 40 + self.__next_motion_duration
            self.__state = LineDriver.SEARCH_LINE_FORWARD_MOTION
            self.__go_inclined_forward(-0.2)
        return False

    def follow_line_start(self) -> None:
        self.__log("follow_line_start:START")
        self.__turn_right()

    def follow_line_update(self) -> int:
        front_match = self.__rgb_front == self.__line_color
        rear_match = self.__rgb_rear == self.__line_color
        left_match = self.__rgb_left == self.__line_color
        right_match = self.__rgb_right == self.__line_color

        current = RelativeToLineState(front_match, rear_match, left_match, right_match)

        # Function to debug line following algorithm. To use:
        # in __init__ enable self.__do_debug_stops and set logger's `off` to False
        def debug_stop(current, sleep_sec: float):
            if not self.__do_debug_stops:
                return

            if current != self.__prev_current:
                self.__stop()
                time.sleep(sleep_sec)

        if current == on_line_end_soon:
            self.__log("LINE END DETECTED")
            self.__go_straight()
            # self.__stop()
            # Should stop now
            # return LineDriver.FOLLOW_LINE_RESULT_FINISH
        elif current == on_line:
            self.__go_straight()
        elif current == on_line_hole:
            self.__log("LINE_HOLE")
            self.__go_straight()
        elif current == on_line_near_left:
            self.__log("NEAR_LEFT")
            # No need to make full rotation, smooth center out
            self.__go_inclined_forward(0.2)
        elif current == on_line_near_right:
            self.__log("NEAR_RIGHT")
            # No need to make full rotation, smooth center out
            self.__go_inclined_forward(-0.2)
        elif current == on_line_too_wide:
            self.__log("TOO_WIDE")
            self.__go_straight()
        elif current == on_line_rear_left:
            self.__log("REAR-LEFT")
            self.__turn_left()
        elif current == on_line_rear_right:
            self.__log("REAR-RIGHT")
            self.__turn_right()
        elif current == off_line:
            self.__log("OFF")
            if self.__prev_current != off_line:
                if random.random() > 0.5:
                    self.__turn_left()
                else:
                    self.__turn_right()
            else:
                self.__stop()
                return LineDriver.FOLLOW_LINE_RESULT_LOST
        elif current == off_line_left_right:
            self.__log("OFF-LEFT-RIGHT")
            debug_stop(current, 1)
            self.__turn_left()
        elif current == on_line_perpendicular:
            self.__log("OFF-LEFT-RIGHT")
            debug_stop(current, 1)
            self.__turn_left()
        elif current == off_line_near_front:
            self.__log("OFF-FRONT")
            debug_stop(current, 1)
            self.__go_straight()
        elif current == off_line_near_front_left:
            self.__log("OFF-FRONT-LEFT")
            debug_stop(current, 1)
            self.__go_inclined_forward(0.2)
        elif current == off_line_near_front_right:
            self.__log("OFF-FRONT-RIGHT")
            debug_stop(current, 1)
            self.__go_inclined_forward(-0.2)
        elif current == off_line_near_left:
            self.__log("OFF-LEFT")
            debug_stop(current, 1)
            self.__turn_left()
        elif current == off_line_near_right:
            self.__log("OFF-RIGHT")
            debug_stop(current, 1)
            self.__turn_right()
        elif current == on_line_perpendicular:
            self.__log("PERPENDICULAR")
            debug_stop(current, 4)
            self.__turn_left()
        self.__prev_current = current
        return LineDriver.FOLLOW_LINE_RESULT_CONTINUE


PortWrapper = TypeVar("PortWrapper", bound=Wrapper)


class PortCollection(Generic[PortWrapper]):
    """
    Provides named access to a list of ports.

    Used by blockly to access ports by mobile-configured names.
    """

    def __init__(self, ports: list[PortWrapper]):
        self._ports = ports
        self._alias_map: dict[str, int] = {}

    @property
    def aliases(self) -> dict[str, int]:
        return self._alias_map

    def __getitem__(self, item: Union[int, str]) -> PortWrapper:
        if type(item) is str:
            # access by name
            if item in self._alias_map.keys():
                item = self._alias_map[item]
            else:
                key_list = self._alias_map.keys()
                raise KeyError(f"key '{item}' not found in alias map. Available keys: {key_list}")

        assert type(item) is int

        try:
            return self._ports[item]
        except IndexError as e:
            raise IndexError(f"Port index out of range: {item}") from e

    def __iter__(self) -> Iterator[PortWrapper]:
        return self._ports.__iter__()


class RobotWrapper:
    """Wrapper class that exposes API to user-written scripts"""

    def __init__(
        self,
        script: "ScriptHandle",
        robot: "Robot",
        config: "RobotConfig",
        resources: dict,
    ):
        self._robot = robot
        self.log = get_logger("RobotWrapper", base=script.log)

        motor_wrappers = [
            MotorPortWrapper(script, port, resources[f"motor_{port.id}"]) for port in robot.motors
        ]
        self._motors = PortCollection(motor_wrappers)
        self._motors.aliases.update(config.motors.names)

        sensor_wrappers = [
            SensorPortWrapper(script, port, resources[f"sensor_{port.id}"])
            for port in robot.sensors
        ]
        self._sensors = PortCollection(sensor_wrappers)
        self._sensors.aliases.update(config.sensors.names)

        self._sound = SoundWrapper(script, robot.sound, resources["sound"])
        self._ring_led = RingLedWrapper(script, robot.led, resources["led_ring"])
        self._drivetrain = DriveTrainWrapper(script, robot.drivetrain, resources["drivetrain"])

        self._script = script

        # shorthand functions
        self.drive = self._drivetrain.drive
        self.turn = self._drivetrain.turn
        self.time = robot.time

    def release_resources(self, none=None) -> None:
        # Sensor wrappers
        for sensor in self._sensors:
            sensor.force_release_resource()

        # Motor wrappers
        for motor in self._motors:
            motor.force_release_resource()

        # Others
        self._sound.force_release_resource()
        self._ring_led.force_release_resource()
        self._drivetrain.force_release_resource()

    @property
    def robot(self) -> "Robot":
        return self._robot

    @property
    def motors(self) -> PortCollection[MotorPortWrapper]:
        return self._motors

    @property
    def sensors(self) -> PortCollection[SensorPortWrapper]:
        return self._sensors

    @property
    def led(self) -> RingLedWrapper:
        return self._ring_led

    @property
    def drivetrain(self) -> DriveTrainWrapper:
        return self._drivetrain

    @property
    def imu(self) -> IMU:
        return self._robot.imu

    @property
    def sound(self) -> SoundWrapper:
        return self._sound

    def play_tune(self, name: str):
        self._sound.play_tune(name)

    def play_note(self) -> None:
        pass  # TODO

    def rotate_for_search(
        self,
        base_color,
        background_color,
        direction: int,
        count_time: int,
        base_speed=0.03,
        stop_line=0,
    ):
        # TODO: if anything, line following is a builtin script, not a robot API.
        # Maybe there's an issue trying to control all this from blockly?
        if direction:
            base_speed = -base_speed
        self._drivetrain.set_speeds(
            map_values(base_speed, 0, 1, 0, 120), map_values(-base_speed, 0, 1, 0, 120)
        )
        count = 0
        while count < count_time:
            count += 1
            sensors = self.read_rgb_sensor_data()
            base_color_, background_color_, line_name_, background_name_, i, colors_gray, colors = (
                detect_line_background_colors(sensors)
            )
            if base_color < background_color:
                base_color = min(base_color_, base_color)
                background_color = max(background_color_, background_color)
            else:
                base_color = max(base_color_, base_color)
                background_color = min(background_color_, background_color)

            forward, left, right, center = colors_gray
            # print("   ", base_color, background_color, "___", forward, left, right, center, "i:", i, colors)
            delta_base_background = abs(background_color - base_color)
            if stop_line:
                if abs(left - right) < 0.12 * (left + right) and (
                    abs(center - base_color) < 0.4 * delta_base_background
                    or abs(forward - base_color) < 0.4 * delta_base_background
                ):
                    self._drivetrain.set_speeds(
                        map_values(0, 0, 1, 0, 120), map_values(0, 0, 1, 0, 120)
                    )
                    return 1, base_color, background_color, line_name_, background_name_
            time.sleep(0.02)
        self._drivetrain.set_speeds(map_values(0, 0, 1, 0, 120), map_values(0, 0, 1, 0, 120))
        time.sleep(0.2)
        return 0, base_color, background_color, None, None

    def search_line(self, line_color: str) -> None:
        log(f"search_line:line_color={line_color}")
        line_driver = LineDriver(self._drivetrain, self, line_color)
        delta_seconds = 0.1
        should_stop = False
        line_driver.search_line_start()
        while not should_stop:
            should_stop = line_driver.search_line_update()
            time.sleep(delta_seconds)
        log("search_line end")
        time.sleep(2)

    def follow_line(self, line_color: str, count_time=10000):
        line_driver = LineDriver(self._drivetrain, self, line_color)
        # interval is 10ms
        delta_seconds = 0.01
        line_driver.follow_line_start()
        STATE_ON_LINE = 0
        STATE_OFF_LINE = 1
        state = STATE_ON_LINE
        off_line_count = 0
        for i in range(count_time):
            if state == STATE_ON_LINE:
                result = line_driver.follow_line_update()
                if result == LineDriver.FOLLOW_LINE_RESULT_FINISH:
                    break
                if result == LineDriver.FOLLOW_LINE_RESULT_CONTINUE:
                    continue
                if result == LineDriver.FOLLOW_LINE_RESULT_LOST:
                    line_driver.search_line_start()
                    state = STATE_OFF_LINE
            elif state == STATE_OFF_LINE:
                # Check if we are too long being off line we need to assume
                # line is over and stop. We give 500ms for that
                off_line_count += 1
                if off_line_count > 50:
                    break

                line_found = line_driver.search_line_update()
                if line_found:
                    off_line_count = 0
                    state = STATE_ON_LINE
                    line_driver.follow_line_start()

            time.sleep(delta_seconds)
        line_driver.stop()

    def debug_print_colors(self, colors: list[ColorData]):
        for i, color in enumerate(colors):
            name = "noname"
            for channel in RGBChannelSensor:
                if i == channel.value:
                    name = color.name
            h = int(color.hue)
            s = int(color.saturation)
            v = int(color.value)
            log(f"{color.red},{color.green},{color.blue}->{h},{s},{v}:{name}")

    def read_rgb_sensor_data(self) -> list[ColorData]:
        sensor_data: ColorSensorReading = self._sensors["color_sensor"].read()

        return [
            rgb_to_hsv_gray(sensor_data.top.r, sensor_data.top.g, sensor_data.top.b),
            rgb_to_hsv_gray(sensor_data.left.r, sensor_data.left.g, sensor_data.left.b),
            rgb_to_hsv_gray(sensor_data.right.r, sensor_data.right.g, sensor_data.right.b),
            rgb_to_hsv_gray(sensor_data.middle.r, sensor_data.middle.g, sensor_data.middle.b),
        ]

    def get_color_by_user_channel(self, user_channel) -> ColorData:
        sensor_channel = user_to_sensor_channel(user_channel)
        if sensor_channel == RGBChannelSensor.UNDEFINED:
            return ColorDataUndefined

        sensors_data_processed = self.read_rgb_sensor_data()
        return sensors_data_processed[sensor_channel.value]

    def read_saturation(self, channel):
        sensor_data = self.get_color_by_user_channel(channel)
        return sensor_data.saturation

    def read_color(self, channel):
        sensor_data = self.get_color_by_user_channel(channel)
        return sensor_data.name

    def read_brightness(self, channel):
        color = self.get_color_by_user_channel(channel)
        return color.value

    def read_hue(self, channel):
        color = self.get_color_by_user_channel(channel)
        return color.hue

    def detects_color(self, color_name, channel):
        color = self.get_color_by_user_channel(channel)
        return color_name == color.name

    def hue_convert(self, val):
        color = self.get_color_by_user_channel(val)
        return "not ready"

    def stop(self):
        pass

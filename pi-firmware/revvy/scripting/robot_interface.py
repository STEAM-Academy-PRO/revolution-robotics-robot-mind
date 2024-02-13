"""
This is the robot's Blockly API.
Whatever code blockly generates, it compiles to python
code that uses these functions.

DANGER!!!!
Do not delete any imports, even if they are not used,
as the generated code MAY use it!

"""
import struct
import time
import random

from functools import partial
from math import floor, sqrt
from numbers import Number
from enum import Enum

from typing import TYPE_CHECKING

# # To have types, use this to avoid circular dependencies.
if TYPE_CHECKING:
    from revvy.scripting.runtime import ScriptHandle
    from revvy.robot_config import RobotConfig


from revvy.robot.configurations import Motors, Sensors
from revvy.robot.led_ring import RingLed
from revvy.robot.ports.motors.base import MotorConstants
from revvy.robot.sound import Sound
from revvy.scripting.resource import Resource
from revvy.scripting.color_functions import rgb_to_hsv_gray,\
    detect_line_background_colors, ColorDataUndefined, color_name_to_rgb

from revvy.utils.functions import hex2rgb
from revvy.robot.ports.common import PortInstance, PortCollection

from revvy.utils.functions import map_values
from revvy.utils.logger import get_logger


log = get_logger('RobotInterface')

class RGBChannelSensor(Enum):
  FRONT     = 0
  LEFT      = 1
  RIGHT     = 2
  REAR      = 3
  UNDEFINED = 4

class UserScriptRGBChannel(Enum):
  FRONT = 1
  RIGHT = 2
  LEFT  = 3
  REAR  = 4


def user_to_sensor_channel(user_channel):
  mapping = [
    (UserScriptRGBChannel.FRONT, RGBChannelSensor.FRONT),
    (UserScriptRGBChannel.LEFT , RGBChannelSensor.LEFT),
    (UserScriptRGBChannel.RIGHT, RGBChannelSensor.RIGHT),
    (UserScriptRGBChannel.REAR , RGBChannelSensor.REAR),
  ]
  for user, sensor in mapping:
    if user_channel == user.value:
      return sensor

  log(f'user_to_sensor_channel: {user_channel}')
  return RGBChannelSensor.UNDEFINED


class ResourceWrapper:
    def __init__(self, resource: Resource, priority=0):
        self._resource = resource
        self._priority = priority
        self._current_handle = None

    def _release_handle(self):
        self._current_handle = None

    def request(self, callback=None):
        if self._current_handle:
            return self._current_handle

        handle = self._resource.request(self._priority, callback)
        if handle:
            handle.on_interrupted.add(self._release_handle)
            handle.on_released.add(self._release_handle)

            self._current_handle = handle

        return self._current_handle

    def release(self):
        handle = self._current_handle
        if handle:
            handle.interrupt()


class Wrapper:
    def __init__(self, script: 'ScriptHandle', resource: ResourceWrapper):
        self._resource = resource
        self._script = script

    def sleep(self, s):
        self._script.sleep(s)

    def try_take_resource(self, callback=None):
        if self._script.is_stop_requested:
            raise InterruptedError

        return self._resource.request(callback)

    def using_resource(self, callback):
        self.if_resource_available(lambda res: res.run_uninterruptable(callback))

    def if_resource_available(self, callback):
        # If the resource is not available, try_take_resource returns None.
        resource_ctx = self.try_take_resource()
        if resource_ctx:
            with resource_ctx as resource:
                callback(resource)

class SensorPortWrapper(Wrapper):
    """Wrapper class to expose sensor ports to user scripts"""

    _named_configurations = {
        'NotConfigured': None,
        'BumperSwitch': Sensors.BumperSwitch,
        'HC_SR04': Sensors.Ultrasonic,
        'RGB': Sensors.SofteqCS,
    }

    def __init__(self, script, sensor: PortInstance, resource: ResourceWrapper):
        super().__init__(script, resource)
        self._sensor = sensor

    def configure(self, config):
        if type(config) is str:
            self._script.log("Warning: Using deprecated named sensor configuration")
            config = self._named_configurations[config]
        self.using_resource(partial(self._sensor.configure, config))

    def read(self):
        """Return the last converted value"""
        if self._script.is_stop_requested:
            raise InterruptedError

        while not self._sensor.has_data:
            self.sleep(0.1)

        return self._sensor.value


def color_string_to_rgb(color_string):
    """ Interface can accept colot_string in several formats
    this can be a hex value like #or actual color name like 'red' or 'black'"""

    result = color_name_to_rgb(color_string)
    if result is not None:
        return result

    if color_string.startswith('#'):
        return hex2rgb(color_string)

    print(f'Color string format not recognised: {color_string}')
    return None


class RingLedWrapper(Wrapper):
    """Wrapper class to expose LED ring to user scripts"""

    def __init__(self, script, ring_led: RingLed, resource: ResourceWrapper):
        super().__init__(script, resource)
        self._ring_led = ring_led
        self._user_leds = [0] * ring_led.count

    @property
    def scenario(self):
        return self._ring_led.scenario

    def start_animation(self, scenario):
        self.using_resource(partial(self._ring_led.start_animation, scenario))

    def set(self, leds: list, color):
        """ Instead of just failing, use the MOD if an LED index is out of range """

        # print(f'RingLedWrapper: set leds:{leds}, color:{color}')
        # def out_of_range(led_idx):
        #     return not 0 < led_idx <= len(self._user_leds)

        # if any(map(out_of_range, leds)):
        #     raise IndexError(f'Led index must be between 1 and {len(self._user_leds)}')

        rgb = color_string_to_rgb(color)

        for idx in leds:
            index = (floor(idx) - 1) % len(self._user_leds)
            # log(f'led {idx} = {index} col {rgb} len {len(self._user_leds)}')
            self._user_leds[index] = rgb

        self.using_resource(partial(self._ring_led.display_user_frame, self._user_leds))


class MotorPortWrapper(Wrapper):
    """Wrapper class to expose motor ports to user scripts"""
    max_rpm = 150
    timeout = 5

    _named_configurations = {
        'NotConfigured': None,
        'RevvyMotor': Motors.RevvyMotor,
        'RevvyMotor_CCW': Motors.RevvyMotor_CCW
    }

    def __init__(self, script: 'ScriptHandle', motor: PortInstance, resource: ResourceWrapper):
        super().__init__(script, resource)
        self._log_prefix = f"MotorPortWrapper[motor {motor.id}]: "
        self._motor = motor

    @property
    def pos(self):
        return self._motor.driver.pos

    @pos.setter
    def pos(self, val):
        self._motor.pos = val

    def log(self, message):
        self._script.log(self._log_prefix + message)

    def configure(self, config):
        if type(config) is str:
            self._script.log("Warning: Using deprecated named motor configuration")
            config = self._named_configurations[config]

        if self._script.is_stop_requested:
            raise InterruptedError

        self._motor.configure(config)

    def move(self, direction, amount, unit_amount, limit, unit_limit):
        self.log("move")
        if unit_amount == MotorConstants.UNIT_ROT:
            unit_amount = MotorConstants.UNIT_DEG
            amount *= 360

        set_fns = {
            MotorConstants.UNIT_DEG: {
                MotorConstants.UNIT_SPEED_RPM: {
                    MotorConstants.DIRECTION_FWD: lambda: self._motor.set_position(amount,
                                                                                   speed_limit=limit,
                                                                                   pos_type='relative'),
                    MotorConstants.DIRECTION_BACK: lambda: self._motor.set_position(-amount,
                                                                                    speed_limit=limit,
                                                                                    pos_type='relative'),
                },
                MotorConstants.UNIT_SPEED_PWR: {
                    MotorConstants.DIRECTION_FWD: lambda: self._motor.set_position(amount, power_limit=limit,
                                                                                   pos_type='relative'),
                    MotorConstants.DIRECTION_BACK: lambda: self._motor.set_position(-amount, power_limit=limit,
                                                                                    pos_type='relative')
                }
            },

            MotorConstants.UNIT_SEC: {
                MotorConstants.UNIT_SPEED_RPM: {
                    MotorConstants.DIRECTION_FWD: lambda: self._motor.set_speed(limit),
                    MotorConstants.DIRECTION_BACK: lambda: self._motor.set_speed(-limit),
                },
                MotorConstants.UNIT_SPEED_PWR: {
                    MotorConstants.DIRECTION_FWD: lambda: self._motor.set_power(limit),
                    MotorConstants.DIRECTION_BACK: lambda: self._motor.set_power(-limit),
                }
            }
        }

        awaiter = None

        def _interrupted():
            self.log('interrupted')
            if awaiter:
                awaiter.cancel()

        with self.try_take_resource(_interrupted) as resource:
            if resource:
                self.log("start movement")
                awaiter = resource.run_uninterruptable(set_fns[unit_amount][unit_limit][direction])

                if unit_amount == MotorConstants.UNIT_DEG:
                    # wait for movement to finish
                    awaiter.wait()

                elif unit_amount == MotorConstants.UNIT_SEC:
                    self.sleep(amount)
                    resource.run_uninterruptable(partial(self._motor.set_power, 0))
                self.log("movement finished")

    def spin(self, direction, rotation, unit_rotation):
        # start moving depending on limits
        self.log("spin")
        set_speed_fns = {
            MotorConstants.UNIT_SPEED_RPM: {
                MotorConstants.DIRECTION_FWD: lambda: self._motor.set_speed(rotation),
                MotorConstants.DIRECTION_BACK: lambda: self._motor.set_speed(-rotation)
            },
            MotorConstants.UNIT_SPEED_PWR: {
                MotorConstants.DIRECTION_FWD: lambda: self._motor.set_power(rotation),
                MotorConstants.DIRECTION_BACK: lambda: self._motor.set_power(-rotation)
            }
        }

        self.using_resource(set_speed_fns[unit_rotation][direction])

    def stop(self, action):
        self.using_resource(partial(self._motor.stop, action))


def wrap_async_method(owner, method):
    def _wrapper(*args, **kwargs):
        def _interrupted():
            if awaiter:
                awaiter.cancel()

        with owner.try_take_resource(_interrupted) as resource:
            if resource:
                awaiter = method(*args, **kwargs)
                if awaiter:
                    awaiter.wait()

    return _wrapper


def wrap_sync_method(owner, method):
    def _wrapper(*args, **kwargs):
        with owner.try_take_resource() as resource:
            if resource:
                method(*args, **kwargs)

    return _wrapper


class DriveTrainWrapper(Wrapper):
    def __init__(self, script, drivetrain, resource: ResourceWrapper):
        super().__init__(script, resource)
        self.__drivetrain = drivetrain
        self.turn = wrap_async_method(self, self.__drivetrain.turn)
        self.drive = wrap_async_method(self, self.__drivetrain.drive)

    def __log(self, message):
        self._script.log("DriveTrain: " + message)

    def set_speed(self, direction, speed, unit_speed=MotorConstants.UNIT_SPEED_RPM):
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

    def set_speeds(self, sl, sr):
        resource = self.try_take_resource()
        if resource:
            try:
                self.__drivetrain.set_speeds(sl, sr)
            finally:
                if sl == sr == 0:
                    resource.release()


class SoundWrapper(Wrapper):
    def __init__(self, script, sound: Sound, resource: ResourceWrapper):
        super().__init__(script, resource)
        self._sound = sound

        self.set_volume = sound.set_volume
        self._is_playing = False

    def _sound_finished(self):
        # this runs on a different thread independent of the script
        self._is_playing = False

    def _play(self, name):
        if not self._is_playing:
            self._is_playing = True  # one sound per thread at the same time
            self._sound.play_tune(name, self._sound_finished)

    def play_tune(self, name):
        # immediately releases resource after starting the playback
        self.if_resource_available(lambda _: self._play(name))

class RelativeToLineState:
    def __init__(self, front, rear, left ,right):
        self.front = front
        self.rear = rear
        self.left = left
        self.right = right

    def __eq__(self, obj):
        if not isinstance(obj, RelativeToLineState):
            return False

        return self.front == obj.front and self.rear == obj.rear and self.left == obj.left and self.right == obj.right


on_line                   = RelativeToLineState(1, 1, 0, 0)
on_line_end_soon          = RelativeToLineState(0, 1, 0, 0)
on_line_near_left         = RelativeToLineState(1, 1, 0, 1)
on_line_near_right        = RelativeToLineState(1, 1, 1, 0)
on_line_too_wide          = RelativeToLineState(1, 1, 1, 1)
on_line_hole              = RelativeToLineState(1, 0, 1, 1)
on_line_perpendicular     = RelativeToLineState(0, 1, 1, 1)
on_line_rear_left         = RelativeToLineState(0, 1, 1, 0)
on_line_rear_right        = RelativeToLineState(0, 1, 0, 1)
off_line                  = RelativeToLineState(0, 0, 0, 0)
off_line_near_front       = RelativeToLineState(1, 0, 0, 0)
off_line_near_front_left  = RelativeToLineState(1, 0, 1, 0)
off_line_near_front_right = RelativeToLineState(1, 0, 0, 1)
off_line_near_left        = RelativeToLineState(0, 0, 1, 0)
off_line_near_right       = RelativeToLineState(0, 0, 0, 1)
off_line_left_right       = RelativeToLineState(0, 0, 1, 1)


class LineDriver:
    FOLLOW_LINE_RESULT_CONTINUE = 0
    FOLLOW_LINE_RESULT_LOST     = 1
    FOLLOW_LINE_RESULT_FINISH   = 2
    SEARCH_LINE_FORWARD_MOTION = 0
    SEARCH_LINE_ROTATE_90 = 1
    def __init__(self, drivetrain, color_reader, line_color):
        self.__drivetrain = drivetrain
        self.__color_reader = color_reader
        self.__line_color = line_color
        self.__search_line_motion_time = 0
        self.__search_line_state_duration = 0
        self.__next_motion_duration = 0
        self.__prev_current = None
        self.__show_debug_msg = False
        self.__do_debug_stops = False
        self.__base_speed = 20
        self.__straight_speed_mult = 1.5
        self.__log = get_logger('LineDriver')

    def __log_debug(self, msg):
        if self.__show_debug_msg:
            self.__log(msg)

    @property
    def __rgb_front(self):
        sensors = self.__color_reader.read_rgb_sensor_data()
        return sensors[RGBChannelSensor.FRONT.value].name

    @property
    def __rgb_left(self):
        sensors = self.__color_reader.read_rgb_sensor_data()
        return sensors[RGBChannelSensor.LEFT.value].name

    @property
    def __rgb_right(self):
        sensors = self.__color_reader.read_rgb_sensor_data()
        return sensors[RGBChannelSensor.RIGHT.value].name

    @property
    def __rgb_rear(self):
        sensors = self.__color_reader.read_rgb_sensor_data()
        return sensors[RGBChannelSensor.REAR.value].name

    def __go_inclined_forward(self, inclination):
        self.__log_debug('INCLINED_FORWARD')
        speed_left = speed_right = self.__base_speed * self.__straight_speed_mult
        if inclination < 0:
            speed_left -= self.__base_speed * (-inclination)
        else:
            speed_right -= self.__base_speed * inclination
        self.__drivetrain.set_speeds(speed_left, speed_right)

    def __turn_left(self):
        self.__log_debug('TURN_LEFT')
        self.__drivetrain.set_speeds(
          self.__base_speed * -0.25,
          self.__base_speed)

    def __turn_right(self):
        self.__log_debug('TURN_RIGHT')
        self.__drivetrain.set_speeds(
          self.__base_speed,
          self.__base_speed * -0.25)

    def __go_straight(self):
        self.__log_debug('GO_STRAIGHT')
        speed = self.__base_speed * self.__straight_speed_mult
        self.__drivetrain.set_speeds(speed, speed)

    def __stop(self):
        self.__log_debug('STOP')
        self.__drivetrain.set_speeds(0, 0)

    def stop(self):
        self.__stop()

    def search_line_start(self):
        self.__log('search_line_start')
        self.__state = LineDriver.SEARCH_LINE_ROTATE_90
        self.__search_line_motion_time = 0
        self.__search_line_state_duration = 1

    # Returns True if line is found,
    # False is line is not found
    def search_line_update(self):
        front_match = self.__rgb_front == self.__line_color
        rear_match  = self.__rgb_rear  == self.__line_color
        left_match  = self.__rgb_left  == self.__line_color
        right_match = self.__rgb_right == self.__line_color
        if front_match or rear_match or left_match or right_match:
            self.__log('search:line_reached')
            self.__stop()
            return True

        self.__search_line_motion_time += 1
        if self.__search_line_motion_time < self.__search_line_state_duration:
            to_go = self.__search_line_state_duration - self.__search_line_motion_time
            self.__log_debug(f'search:state_timeout:{to_go}')
            return False

        self.__search_line_motion_time = 0
        self.__next_motion_duration += 10
        if self.__state == LineDriver.SEARCH_LINE_FORWARD_MOTION:
            self.__log_debug('search::rotate 90')
            self.__search_line_state_duration = 15
            self.__state = LineDriver.SEARCH_LINE_ROTATE_90
            self.__turn_left()
        elif self.__state == LineDriver.SEARCH_LINE_ROTATE_90:
            self.__log_debug('search:inclined forward')
            self.__search_line_state_duration = 40 + self.__next_motion_duration
            self.__state = LineDriver.SEARCH_LINE_FORWARD_MOTION
            self.__go_inclined_forward(-0.2)
        return False

    def follow_line_start(self):
        self.__log('follow_line_start:START')
        self.__turn_right()

    def follow_line_update(self):
        front_match = self.__rgb_front == self.__line_color
        rear_match  = self.__rgb_rear  == self.__line_color
        left_match  = self.__rgb_left  == self.__line_color
        right_match = self.__rgb_right == self.__line_color

        current = RelativeToLineState(front_match, rear_match, left_match, right_match)

        # Function to debug line following algorithm. To use:
        # 1. in __init__ enable self.__do_debug_stops
        # 2. and enable self.__show_debug_msg
        def debug_stop(current, sleep_sec):
            if not self.__do_debug_stops:
                return

            if current != self.__prev_current:
                self.__stop()
                time.sleep(sleep_sec)

        if current == on_line_end_soon:
            self.__log('LINE END DETECTED')
            self.__go_straight()
            # self.__stop()
            # Should stop now
            # return LineDriver.FOLLOW_LINE_RESULT_FINISH
        elif current == on_line:
            self.__go_straight()
        elif current == on_line_hole:
            self.__log_debug('LINE_HOLE')
            self.__go_straight()
        elif current == on_line_near_left:
            self.__log_debug('NEAR_LEFT')
            # No need to make full rotation, smooth center out
            self.__go_inclined_forward(0.2)
        elif current == on_line_near_right:
            self.__log_debug('NEAR_RIGHT')
            # No need to make full rotation, smooth center out
            self.__go_inclined_forward(-0.2)
        elif current == on_line_too_wide:
            self.__log_debug('TOO_WIDE')
            self.__go_straight()
        elif current == on_line_rear_left:
            self.__log_debug('REAR-LEFT')
            self.__turn_left()
        elif current == on_line_rear_right:
            self.__log_debug('REAR-RIGHT')
            self.__turn_right()
        elif current == off_line:
            self.__log_debug('OFF')
            if self.__prev_current != off_line:
                if random.random() > 0.5:
                    self.__turn_left()
                else:
                    self.__turn_right()
            else:
                self.__stop()
                return LineDriver.FOLLOW_LINE_RESULT_LOST
        elif current == off_line_left_right:
            self.__log_debug('OFF-LEFT-RIGHT')
            debug_stop(current, 1)
            self.__turn_left()
        elif current == on_line_perpendicular:
            self.__log_debug('OFF-LEFT-RIGHT')
            debug_stop(current, 1)
            self.__turn_left()
        elif current == off_line_near_front:
            self.__log_debug('OFF-FRONT')
            debug_stop(current, 1)
            self.__go_straight()
        elif current == off_line_near_front_left:
            self.__log_debug('OFF-FRONT-LEFT')
            debug_stop(current, 1)
            self.__go_inclined_forward(0.2)
        elif current == off_line_near_front_right:
            self.__log_debug('OFF-FRONT-RIGHT')
            debug_stop(current, 1)
            self.__go_inclined_forward(-0.2)
        elif current == off_line_near_left:
            self.__log_debug('OFF-LEFT')
            debug_stop(current, 1)
            self.__turn_left()
        elif current == off_line_near_right:
            self.__log_debug('OFF-RIGHT')
            debug_stop(current, 1)
            self.__turn_right()
        elif current == on_line_perpendicular:
            self.__log_debug('PERPENDICULAR')
            debug_stop(current, 4)
            self.__turn_left()
        self.__prev_current = current
        return LineDriver.FOLLOW_LINE_RESULT_CONTINUE


class RobotInterface:
    def time(self):
        raise NotImplementedError

    @property
    def motors(self) -> PortCollection:
        raise NotImplementedError

    @property
    def sensors(self) -> PortCollection:
        raise NotImplementedError

    @property
    def led(self):
        raise NotImplementedError

    @property
    def sound(self):
        raise NotImplementedError

    @property
    def drivetrain(self):
        raise NotImplementedError

    @property
    def imu(self):
        raise NotImplementedError

    def play_tune(self, name):
        raise NotImplementedError


class RobotWrapper(RobotInterface):
    """Wrapper class that exposes API to user-written scripts"""

    def __init__(self, script: 'ScriptHandle', robot: RobotInterface, config: 'RobotConfig', resources: dict, priority=0):
        self._resources = {name: ResourceWrapper(resources[name], priority) for name in resources}
        self._robot = robot

        motor_wrappers = [MotorPortWrapper(script, port, self._resources[f'motor_{port.id}'])
                          for port in robot.motors]
        sensor_wrappers = [SensorPortWrapper(script, port, self._resources[f'sensor_{port.id}'])
                           for port in robot.sensors]
        self._motors = PortCollection(motor_wrappers)
        self._sensors = PortCollection(sensor_wrappers)
        motor_names = config.motors.names
        self._motors.aliases.update(motor_names)
        self._sensors.aliases.update(config.sensors.names)
        self._sound = SoundWrapper(script, robot.sound, self._resources['sound'])
        self._ring_led = RingLedWrapper(script, robot.led, self._resources['led_ring'])
        self._drivetrain = DriveTrainWrapper(script, robot.drivetrain, self._resources['drivetrain'])

        self._script = script

        # shorthand functions
        self.drive = self._drivetrain.drive
        self.turn = self._drivetrain.turn

        self.time = robot.time

    def release_resources(self, none=None):
        for res in self._resources.values():
            res.release()

    def time(self):
        return self._robot.time

    @property
    def robot(self):
        return self._robot

    @property
    def motors(self):
        return self._motors

    @property
    def sensors(self):
        return self._sensors

    @property
    def led(self):
        return self._ring_led

    @property
    def drivetrain(self):
        return self._drivetrain

    @property
    def imu(self):
        return self._robot.imu

    @property
    def sound(self):
        return self._sound

    def play_tune(self, name):
        self._sound.play_tune(name)

    def play_note(self): pass  # TODO

    def rotate_for_search(
            self,
            base_color,
            background_color,
            direction: int,
            count_time: int,
            base_speed=0.03,
            stop_line=0,
    ):
        if direction:
            base_speed = -base_speed
        self._drivetrain.set_speeds(
            map_values(base_speed, 0, 1, 0, 120),
            map_values(-base_speed, 0, 1, 0, 120))
        count = 0
        while count < count_time:
            count += 1
            sensors = self.read_rgb_sensor_data()
            base_color_, background_color_, line_name_, background_name_, i, colors_gray, colors = \
                detect_line_background_colors(sensors)
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
                if abs(left - right) < 0.12 * (left + right) \
                        and (
                        abs(center - base_color) < 0.4 * delta_base_background
                        or abs(forward - base_color) < 0.4 * delta_base_background
                ):
                    self._drivetrain.set_speeds(
                        map_values(0, 0, 1, 0, 120),
                        map_values(0, 0, 1, 0, 120))
                    return 1, base_color, background_color, line_name_, background_name_
            time.sleep(0.02)
        self._drivetrain.set_speeds(
            map_values(0, 0, 1, 0, 120),
            map_values(0, 0, 1, 0, 120))
        time.sleep(0.2)
        return 0, base_color, background_color, None, None

    def search_line(self, line_color):
        log(f'search_line:line_color={line_color}')
        line_driver = LineDriver(self._drivetrain, self, line_color)
        delta_seconds = 0.1
        should_stop = False
        line_driver.search_line_start()
        while not should_stop:
            should_stop = line_driver.search_line_update()
            time.sleep(delta_seconds)
        log('search_line end')
        time.sleep(2)

    def follow_line(self, line_color, count_time=10000):
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


    def debug_print_colors(self, colors):
        for i, color in enumerate(colors):
          name = 'noname'
          for channel in RGBChannelSensor:
            if i == channel.value:
              name = color.name
          h = int(color.hue)
          s = int(color.saturation)
          v = int(color.value)
          log(f'{color.red},{color.green},{color.blue}->{h},{s},{v}:{name}')

    def read_rgb_sensor_data(self):
        res = self._sensors["color_sensor"].read()
        n = len(res)
        if n % 3:
            padding = 3 - n % 3
            res += b'\0' * padding
        result = [rgb_to_hsv_gray(*_) for _ in struct.iter_unpack("<BBB", res)]
        # self.debug_print_colors(result)
        return result

    def get_color_by_user_channel(self, user_channel):
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
        return 'not ready'

    def stop(self):
        pass

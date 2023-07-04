# SPDX-License-Identifier: GPL-3.0-only
import struct
import time

from functools import partial
from math import sqrt
from enum import Enum

from revvy.robot.configurations import Motors, Sensors
from revvy.robot.led_ring import RingLed
from revvy.robot.ports.motor import MotorConstants
from revvy.robot.sound import Sound
from revvy.scripting.resource import Resource
from revvy.scripting.color_functions import rgb_to_hsv_gray,\
    detect_line_background_colors, ColorDataUndefined, color_name_to_rgb

from revvy.utils.functions import hex2rgb
from revvy.robot.ports.common import PortInstance, PortCollection

from revvy.utils.functions import map_values


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
  for i in UserScriptRGBChannel:
    if i.value == user_channel:
      return i
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
    def __init__(self, script, resource: ResourceWrapper):
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
        with self.try_take_resource() as resource:
            if resource:
                callback(resource)


class SensorPortWrapper(Wrapper):
    """Wrapper class to expose sensor ports to user scripts"""

    _named_configurations = {
        'NotConfigured': None,
        'BumperSwitch': Sensors.BumperSwitch,
        'HC_SR04': Sensors.Ultrasonic,
        'EV3': None,
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
    if result:
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
        # print(f'RingLedWrapper: set leds:{leds}, color:{color}')
        def out_of_range(led_idx):
            return not 0 < led_idx <= len(self._user_leds)

        if any(map(out_of_range, leds)):
            raise IndexError(f'Led index must be between 1 and {len(self._user_leds)}')

        rgb = color_string_to_rgb(color)
        # print(f'color_string_to_rgb: {color}->{rgb}')

        for idx in leds:
            self._user_leds[idx - 1] = rgb

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

    def __init__(self, script, motor: PortInstance, resource: ResourceWrapper):
        super().__init__(script, resource)
        self._log_prefix = f"MotorPortWrapper[motor {motor.id}]: "
        self._motor = motor

    @property
    def pos(self):
        return self._motor.pos

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
        self._drivetrain = drivetrain

        self.turn = wrap_async_method(self, drivetrain.turn)
        self.drive = wrap_async_method(self, drivetrain.drive)

    def log(self, message):
        self._script.log("DriveTrain: " + message)

    def set_speed(self, direction, speed, unit_speed=MotorConstants.UNIT_SPEED_RPM):
        self.log("set_speed")

        resource = self.try_take_resource()
        if resource:
            try:
                self._drivetrain.set_speed(direction, speed, unit_speed)
            finally:
                if speed == 0:
                    resource.release()

    def set_speeds(self, sl, sr):
        resource = self.try_take_resource()
        if resource:
            try:
                self._drivetrain.set_speeds(sl, sr)
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

    # FIXME: type hints missing because of circular reference that causes ImportError
    def __init__(self, script, robot: RobotInterface, config, res: dict, priority=0):
        self._resources = {name: ResourceWrapper(res[name], priority) for name in res}
        self._robot = robot

        motor_wrappers = [MotorPortWrapper(script, port, self._resources[f'motor_{port.id}'])
                          for port in robot.motors]
        sensor_wrappers = [SensorPortWrapper(script, port, self._resources[f'sensor_{port.id}'])
                           for port in robot.sensors]
        self._motors = PortCollection(motor_wrappers)
        self._sensors = PortCollection(sensor_wrappers)
        self._motors.aliases.update(config.motors.names)
        self._sensors.aliases.update(config.sensors.names)
        self._sound = SoundWrapper(script, robot.sound, self._resources['sound'])
        self._ring_led = RingLedWrapper(script, robot.led, self._resources['led_ring'])
        self._drivetrain = DriveTrainWrapper(script, robot.drivetrain, self._resources['drivetrain'])

        self._script = script

        # shorthand functions
        self.drive = self._drivetrain.drive
        self.turn = self._drivetrain.turn

        self.time = robot.time

    def release_resources(self):
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
        raise self._sound

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
            res = self._sensors["color_sensor"].read()
            sensors = [rgb_to_hsv_gray(*_) for _ in struct.iter_unpack("<BBB", res)]
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

    def search_line(self, val):
        """ searches current line and background colors
        when finished color sensor should be at the center of line (left color == right color)"""

        res = self._sensors["color_sensor"].read()
        sensors_data = [rgb_to_hsv_gray(*_) for _ in struct.iter_unpack("<BBB", res)]

        base_color, background_color, line_name, background_name, i, colors, colors_gray = \
            detect_line_background_colors(sensors_data)

        status, base_color, background_color, line_color_name, _ = self.rotate_for_search(
            base_color, background_color, 0, 40, 0.03, 0
        )
        status, base_color, background_color, line_color_name, _ = self.rotate_for_search(
            base_color, background_color, 1, 120, 0.03, 0
        )
        status, base_color, background_color, line_color_name, _ = self.rotate_for_search(
            base_color, background_color, 0, 160, 0.03, 1
        )
        return base_color, background_color, line_color_name

    def follow_line(self,
                    base_color=0, background_color=0, line_name='not_defined',
                    count_time=100, base_speed=0.2,
                    func_search_lr=None, desired_color='', side='',
                    ):
        """ need to set correct line and background colors, this colors we need to get from search_color function
        it is function for step 3"""

        if base_color == 0 or background_color == 0 or line_name == 'not_defined':
            print("line_gray:", base_color, "background_gray:", background_color, "line_color_name:", line_name)
            return 2
        count = 0
        k_speed = 1 - 0.23 * base_speed
        if k_speed > 0.99:
            k_speed = 0.99

        while count < count_time:  # 500 800:
            count += 1
            # get colors
            res = self._sensors["color_sensor"].read()
            sensors = [rgb_to_hsv_gray(*_) for _ in struct.iter_unpack("<BBB", res)]
            base_color_, background_color_, line_name_, background_name_, i, colors_gray, colors = \
                detect_line_background_colors(sensors)

            forward, left, right, center = colors_gray
            forward_name, left_name, right_name, center_name = colors
            print("   ", base_color, background_color, "___", forward, left, right, center, "___", colors)

            delta_base_background = abs(background_color - base_color)
            delta = delta_base_background * 1.03

            # check: stop when line loosed and exit from function
            param = delta_base_background * 0.4
            if not (abs(base_color - forward) < param or abs(base_color - center) < param
                    or abs(base_color - right) < param or abs(base_color - left) < param):
                drivetrain_control.set_speeds(
                    map_values(0, 0, 1, 0, 120),
                    map_values(0, 0, 1, 0, 120))
                print("stop, line loosed")
                return 1

            # check left/right lines
            if func_search_lr:
                if func_search_lr(colors, desired_color, side):
                    self._drivetrain.set_speeds(
                        map_values(0, 0, 1, 0, 120),
                        map_values(0, 0, 1, 0, 120))
                    print("stop, line found")
                    return 0

            forward_level = 0.35  # 0.40 good for base_speed = 0.2
            k_forward = 0
            temp = abs(forward - base_color) / delta_base_background
            if temp > 0.25:
                k_forward = forward_level * temp
            k_angle = 1.02 + sqrt(delta_base_background / 6.8)  # 7.0 good for base_speed = 0.2
            sl = base_speed
            sr = base_speed
            delta_lr = abs(right - left)
            k_diff = (1 - k_speed) + k_speed * ((k_angle * sqrt(abs(delta - delta_lr)) + (
                    delta_base_background - k_angle * sqrt(delta))) / delta)

            if forward_name == line_name:
                k_forward = 0

            k_diff = k_diff * (1 - k_forward)

            speed_primary = base_speed * k_diff  # * 0.9
            speed_secondary = base_speed / k_diff

            compare = delta_base_background / 40  # /20  # !!!!!!!!!!
            if delta_lr > compare:
                sr = speed_primary
                sl = speed_secondary
                if base_color > background_color:
                    sr = speed_secondary
                    sl = speed_primary
                str_turn = "          >>>>>>>>>>>"
                if right > left:
                    sl = speed_primary
                    sr = speed_secondary
                    if base_color > background_color:
                        sl = speed_secondary
                        sr = speed_primary
                    str_turn = "          <<<<<<<<<<<"
                print(str_turn)
            # check overspeed
            if sl > 1:
                sl = 0
                count = count_time
            if sr > 1:
                sr = 0
                count = count_time
            # set calculated speeds
            self._drivetrain.set_speeds(
                map_values(sl, 0, 1, 0, 120),
                map_values(sr, 0, 1, 0, 120))
            time.sleep(0.015)

        # stop at end of function
        self._drivetrain.set_speeds(
            map_values(0, 0, 1, 0, 120),
            map_values(0, 0, 1, 0, 120))
        return 3

    def debug_print_colors(self, colors):
        for i, color in enumerate(colors):
          name = 'noname'
          for channel in RGBChannelSensor:
            if i == channel.value:
              name = color.name
          h = int(color.hue)
          s = int(color.saturation)
          v = int(color.value)
          print(f'{color.red},{color.green},{color.blue}->{h},{s},{v}:{name}')

    def get_color_by_user_channel(self, user_channel):
        sensor_channel = user_to_sensor_channel(user_channel)
        if sensor_channel == RGBChannelSensor.UNDEFINED:
          return ColorDataUndefined

        res = self._sensors["color_sensor"].read()
        sensors_data_raw = list(struct.iter_unpack("<BBB", res))
        sensors_data_processed = [rgb_to_hsv_gray(*_) for _ in sensors_data_raw]
        # self.debug_print_colors(sensors_data_processed)
        return sensors_data_processed[sensor_channel.value]

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
        color = self.get_color_by_user_channel(channel)
        return 'not ready'

    def stop(self):
        pass

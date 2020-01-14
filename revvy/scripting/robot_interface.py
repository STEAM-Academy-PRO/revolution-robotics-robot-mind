# SPDX-License-Identifier: GPL-3.0-only

import time

from revvy.robot.configurations import Motors, Sensors
from revvy.robot.led_ring import RingLed
from revvy.robot.sound import Sound
from revvy.scripting.resource import Resource
from revvy.utils.functions import hex2rgb
from revvy.robot.ports.common import PortInstance, PortCollection


class ResourceWrapper:
    def __init__(self, resource: Resource, priority=0):
        self._resource = resource
        self._priority = priority

    def request(self):
        return self._resource.request(self._priority)


class Wrapper:
    def __init__(self, script, resource: ResourceWrapper):
        self._resource = resource
        self._script = script

        self.sleep = script.sleep

    def try_take_resource(self):
        if self._script.is_stop_requested:
            raise InterruptedError

        return self._resource.request()

    def using_resource(self, callback):
        self.if_resource_available(lambda res: res.run_uninterruptable(callback))

    def if_resource_available(self, callback):
        resource = self.try_take_resource()
        if resource:
            try:
                callback(resource)
            finally:
                resource.release()


class SensorPortWrapper(Wrapper):
    """Wrapper class to expose sensor ports to user scripts"""

    _named_configurations = {
        'BumperSwitch': Sensors.BumperSwitch,
        'HC_SR04': Sensors.HC_SR04
    }

    def __init__(self, script, sensor: PortInstance, resource: ResourceWrapper):
        super().__init__(script, resource)
        self._sensor = sensor

    def configure(self, config):
        if type(config) is str:
            self._script.log("Warning: Using deprecated named sensor configuration")
            config = self._named_configurations[config]
        self.using_resource(lambda: self._sensor.configure(config))

    def read(self):
        """Return the last converted value"""
        while not self._sensor.has_data:
            self.sleep(0.1)

        return self._sensor.value


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
        self.using_resource(lambda: self._ring_led.start_animation(scenario))

    def set(self, led_index, color):
        if type(led_index) is not list:
            led_index = [led_index]

        rgb = hex2rgb(color)

        for idx in led_index:
            if not (1 <= idx <= self._ring_led.count):
                raise IndexError('Led index invalid: {}'.format(idx))
            self._user_leds[idx - 1] = rgb

        self.using_resource(lambda: self._ring_led.display_user_frame(self._user_leds))


class MotorConstants:
    DIRECTION_FWD = 0
    DIRECTION_BACK = 1
    DIRECTION_LEFT = 2
    DIRECTION_RIGHT = 3

    UNIT_ROT = 0
    UNIT_SEC = 1
    UNIT_DEG = 2
    UNIT_TURN_ANGLE = 3

    UNIT_SPEED_RPM = 0
    UNIT_SPEED_PWR = 1

    ACTION_STOP_AND_HOLD = 0
    ACTION_RELEASE = 1


def rpm2dps(rpm):
    """
    >>> rpm2dps(1)
    6
    >>> rpm2dps(60)
    360
    """
    return rpm * 6


class MotorPortWrapper(Wrapper):
    """Wrapper class to expose motor ports to user scripts"""
    max_rpm = 150
    timeout = 5

    _named_configurations = {
        'RevvyMotor': Motors.RevvyMotor,
        'RevvyMotor_CCW': Motors.RevvyMotor_CCW
    }

    def __init__(self, script, motor: PortInstance, resource: ResourceWrapper):
        super().__init__(script, resource)
        self.log = lambda message: script.log("MotorPortWrapper[motor {}]: {}".format(motor.id, message))
        self._motor = motor

    def configure(self, config):
        if type(config) is str:
            self._script.log("Warning: Using deprecated named motor configuration")
            config = self._named_configurations[config]
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
                                                                                   speed_limit=rpm2dps(limit),
                                                                                   pos_type='relative'),
                    MotorConstants.DIRECTION_BACK: lambda: self._motor.set_position(-amount,
                                                                                    speed_limit=rpm2dps(limit),
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
                    MotorConstants.DIRECTION_FWD: lambda: self._motor.set_speed(rpm2dps(limit)),
                    MotorConstants.DIRECTION_BACK: lambda: self._motor.set_speed(rpm2dps(-limit)),
                },
                MotorConstants.UNIT_SPEED_PWR: {
                    MotorConstants.DIRECTION_FWD: lambda: self._motor.set_power(limit),
                    MotorConstants.DIRECTION_BACK: lambda: self._motor.set_power(-limit),
                }
            }
        }

        resource = self.try_take_resource()
        if resource:
            try:
                self.log("start movement")
                resource.run_uninterruptable(set_fns[unit_amount][unit_limit][direction])

                if unit_amount == MotorConstants.UNIT_DEG:
                    # wait for movement to finish
                    self.sleep(0.2)

                    start_pos = self._motor.position
                    start_time = time.time()
                    while not resource.is_interrupted and self._motor.is_moving:

                        # check if there was any movement
                        if time.time() - start_time > 1:
                            pos = self._motor.position
                            pos_diff = pos - start_pos
                            start_pos = pos

                            if direction == MotorConstants.DIRECTION_BACK:
                                pos_diff *= -1

                            if pos_diff > 0:
                                # there was a positive movement towards the goal, reset timeout
                                self.log("movement detected, reset timeout: {}")
                                start_time = time.time()

                        # check movement timeout
                        if time.time() - start_time > self.timeout:
                            # no need to force the motors, stop
                            resource.run_uninterruptable(lambda: self._motor.set_power(0))
                            self.log("timeout")
                            break

                        self.sleep(0.2)

                elif unit_amount == MotorConstants.UNIT_SEC:
                    self.sleep(amount)
                    resource.run_uninterruptable(lambda: self._motor.set_speed(0))

            finally:
                resource.release()
            self.log("movement finished")

    def spin(self, direction, rotation, unit_rotation):
        # start moving depending on limits
        self.log("spin")
        set_speed_fns = {
            MotorConstants.UNIT_SPEED_RPM: {
                MotorConstants.DIRECTION_FWD: lambda: self._motor.set_speed(rpm2dps(rotation)),
                MotorConstants.DIRECTION_BACK: lambda: self._motor.set_speed(rpm2dps(-rotation))
            },
            MotorConstants.UNIT_SPEED_PWR: {
                MotorConstants.DIRECTION_FWD: lambda: self._motor.set_speed(rpm2dps(self.max_rpm),
                                                                            power_limit=rotation),
                MotorConstants.DIRECTION_BACK: lambda: self._motor.set_speed(rpm2dps(-self.max_rpm),
                                                                             power_limit=rotation)
            }
        }

        self.using_resource(set_speed_fns[unit_rotation][direction])

    def stop(self, action):
        self.log("stop")
        stop_fn = {
            MotorConstants.ACTION_STOP_AND_HOLD: lambda: self._motor.set_speed(0),
            MotorConstants.ACTION_RELEASE: lambda: self._motor.set_power(0),
        }
        self.using_resource(stop_fn[action])


class DriveTrainWrapper(Wrapper):
    max_rpm = 150
    timeout = 5
    turn_timeout = 10

    def __init__(self, script, drivetrain, resource: ResourceWrapper):
        super().__init__(script, resource)
        self.log = lambda message: script.log("DriveTrain: {}".format(message))
        self._drivetrain = drivetrain

    def drive(self, direction, rotation, unit_rotation, speed, unit_speed):
        self.log("drive")
        multipliers = {
            MotorConstants.DIRECTION_FWD:   1,
            MotorConstants.DIRECTION_BACK: -1,
        }

        set_fns = {
            MotorConstants.UNIT_ROT: {
                MotorConstants.UNIT_SPEED_RPM: lambda: self._drivetrain.move(
                    360 * rotation * multipliers[direction],
                    360 * rotation * multipliers[direction],
                    left_speed=rpm2dps(speed),
                    right_speed=rpm2dps(speed)),

                MotorConstants.UNIT_SPEED_PWR: lambda: self._drivetrain.move(
                    360 * rotation * multipliers[direction],
                    360 * rotation * multipliers[direction],
                    power_limit=speed)
            },
            MotorConstants.UNIT_SEC: {
                MotorConstants.UNIT_SPEED_RPM: lambda: self._drivetrain.set_speeds(
                    rpm2dps(speed) * multipliers[direction],
                    rpm2dps(speed) * multipliers[direction]),

                MotorConstants.UNIT_SPEED_PWR: lambda: self._drivetrain.set_speeds(
                    rpm2dps(self.max_rpm) * multipliers[direction],
                    rpm2dps(self.max_rpm) * multipliers[direction],
                    power_limit=speed)
            }
        }

        resource = self.try_take_resource()
        if resource:
            try:
                self.log("start movement")
                resource.run_uninterruptable(set_fns[unit_rotation][unit_speed])

                if unit_rotation == MotorConstants.UNIT_ROT:
                    # wait for movement to finish

                    start_positions = [motor.position for motor in self._drivetrain.motors]
                    start_time = time.time()

                    if direction == MotorConstants.DIRECTION_BACK:
                        mult = -1
                    else:
                        mult = 1

                    self.sleep(0.2)
                    while not resource.is_interrupted and self._drivetrain.is_moving:

                        # check if there was any movement
                        if time.time() - start_time > 1:
                            i = 0

                            for motor in self._drivetrain.motors:
                                pos = motor.position
                                pos_diff = pos - start_positions[i]
                                start_positions[i] = pos

                                if pos_diff * mult > 0:
                                    # there was movement towards the goal, reset timeout
                                    self.log("movement detected, reset timeout")
                                    start_time = time.time()

                                i += 1

                        # check movement timeout
                        if time.time() - start_time > self.timeout:
                            self.log("timeout")
                            break

                        self.sleep(0.2)

                    if not resource.is_interrupted:
                        resource.run_uninterruptable(lambda: self._drivetrain.set_speeds(0, 0))
                        self.sleep(0.2)

                elif unit_rotation == MotorConstants.UNIT_SEC:
                    self.sleep(rotation)

                    resource.run_uninterruptable(lambda: self._drivetrain.set_speeds(0, 0))

            finally:
                self.log("movement finished")
                resource.release()

    def turn(self, direction, rotation, unit_rotation, speed, unit_speed):
        self.log("turn")
        left_multipliers = {
            MotorConstants.DIRECTION_LEFT: -1,
            MotorConstants.DIRECTION_RIGHT: 1,
        }
        right_multipliers = {
            MotorConstants.DIRECTION_LEFT:  1,
            MotorConstants.DIRECTION_RIGHT: -1,
        }
        turn_multipliers = {
            MotorConstants.DIRECTION_LEFT:  1,  # +ve number -> CCW turn
            MotorConstants.DIRECTION_RIGHT: -1,  # -ve number -> CW turn
        }

        set_fns = {
            MotorConstants.UNIT_SEC: {
                MotorConstants.UNIT_SPEED_RPM: lambda: self._drivetrain.set_speeds(
                    rpm2dps(speed) * left_multipliers[direction],
                    rpm2dps(speed) * right_multipliers[direction]),

                MotorConstants.UNIT_SPEED_PWR: lambda: self._drivetrain.set_speeds(
                    rpm2dps(self.max_rpm) * left_multipliers[direction],
                    rpm2dps(self.max_rpm) * right_multipliers[direction],
                    power_limit=speed)
            },
            MotorConstants.UNIT_TURN_ANGLE: {
                MotorConstants.UNIT_SPEED_RPM: lambda: self._drivetrain.turn(
                    rotation * turn_multipliers[direction],
                    rpm2dps(speed)),

                MotorConstants.UNIT_SPEED_PWR: lambda: self._drivetrain.turn(
                    rotation * turn_multipliers[direction],
                    rpm2dps(self.max_rpm),
                    power_limit=speed)
            }
        }

        resource = self.try_take_resource()
        if resource:
            try:
                self.log("start movement")
                resource.run_uninterruptable(set_fns[unit_rotation][unit_speed])

                if unit_rotation == MotorConstants.UNIT_TURN_ANGLE:
                    # wait for movement to finish

                    start_time = time.time()

                    self.sleep(0.2)
                    while not resource.is_interrupted and self._drivetrain.is_moving:
                        if start_time - time.time() > self.turn_timeout:
                            # 10s timeout
                            self.log("timeout")
                            break
                        self.sleep(0.2)

                    if not resource.is_interrupted:
                        resource.run_uninterruptable(lambda: self._drivetrain.set_speeds(0, 0))
                        self.sleep(0.2)

                elif unit_rotation == MotorConstants.UNIT_SEC:
                    self.sleep(rotation)

                    resource.run_uninterruptable(lambda: self._drivetrain.set_speeds(0, 0))

            finally:
                self.log("turn finished")
                resource.release()

    def set_speeds(self, direction, speed, unit_speed=MotorConstants.UNIT_SPEED_RPM):
        self.log("set_speeds")
        multipliers = {
            MotorConstants.DIRECTION_FWD:   1,
            MotorConstants.DIRECTION_BACK: -1,
        }

        resource = self.try_take_resource()
        if resource:
            try:
                if unit_speed == MotorConstants.UNIT_SPEED_RPM:
                    self._drivetrain.set_speeds(
                        multipliers[direction] * rpm2dps(speed),
                        multipliers[direction] * rpm2dps(speed)
                    )
                elif unit_speed == MotorConstants.UNIT_SPEED_PWR:
                    self._drivetrain.set_speeds(
                        multipliers[direction] * rpm2dps(self.max_rpm),
                        multipliers[direction] * rpm2dps(self.max_rpm),
                        power_limit=speed
                    )
            finally:
                if speed == 0:
                    resource.release()


class JoystickWrapper(Wrapper):
    max_rpm = 150

    def __init__(self, script, drivetrain, resource: ResourceWrapper):
        super().__init__(script, resource)
        self.log = lambda message: script.log("Joystick: {}".format(message))
        self._drivetrain = drivetrain
        self._res = None

    def set_speeds(self, sl, sr):
        if self._res:
            # we already have the resource - check if it was taken away
            if self._res.is_interrupted:
                # need to release the stick before re-taking
                if sl == sr == 0:
                    self._res = None
            else:
                # the resource is ours, use it
                self._drivetrain.set_speeds(sl, sr)
                if sl == sr == 0:
                    # manual stop: allow lower priority scripts to move
                    self.log("resource released")
                    self._res.release()
                    self._res = None
        else:
            self._res = self.try_take_resource()
            if self._res:
                try:
                    self.log("resource taken")
                    self._drivetrain.set_speeds(sl, sr)
                finally:
                    if sl == sr == 0:
                        self.log("resource released immediately")
                        self._res.release()
                        self._res = None


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
        self.if_resource_available(lambda resource: self._play(name))


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

        def motor_name(port):
            return 'motor_{}'.format(port.id)

        def sensor_name(port):
            return 'sensor_{}'.format(port.id)

        motor_wrappers = [MotorPortWrapper(script, port, self._resources[motor_name(port)])
                          for port in robot.motors]
        sensor_wrappers = [SensorPortWrapper(script, port, self._resources[sensor_name(port)])
                           for port in robot.sensors]
        self._motors = PortCollection(motor_wrappers)
        self._sensors = PortCollection(sensor_wrappers)
        self._motors.aliases.update(config.motors.names)
        self._sensors.aliases.update(config.sensors.names)
        self._sound = SoundWrapper(script, robot.sound, self._resources['sound'])
        self._ring_led = RingLedWrapper(script, robot.led, self._resources['led_ring'])
        self._drivetrain = DriveTrainWrapper(script, robot.drivetrain, self._resources['drivetrain'])
        self._joystick = JoystickWrapper(script, robot.drivetrain, self._resources['drivetrain'])

        self._script = script

        # shorthand functions
        self.drive = self._drivetrain.drive
        self.turn = self._drivetrain.turn

        self.time = robot.time

    def stop_all_motors(self, action):
        """
        @deprecated
        @param action: MotorConstants.ACTION_STOP_AND_HOLD or MotorConstants.ACTION_RELEASE
        """
        for motor in self._motors:
            motor.stop(action)

    def time(self):
        return self._robot.time

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
    def joystick(self):
        return self._joystick

    @property
    def imu(self):
        return self._robot.imu

    @property
    def sound(self):
        raise self._sound

    def play_tune(self, name):
        self._sound.play_tune(name)

    def play_note(self): pass  # TODO

    def release_resources(self):
        for res in self._resources.values():
            res.interrupt()

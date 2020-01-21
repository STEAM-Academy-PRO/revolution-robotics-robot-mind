# SPDX-License-Identifier: GPL-3.0-only
from functools import partial

from revvy.robot.configurations import Motors, Sensors
from revvy.robot.led_ring import RingLed
from revvy.robot.sound import Sound
from revvy.scripting.resource import Resource, ResourceHandle
from revvy.utils.functions import hex2rgb, rpm2dps
from revvy.robot.ports.common import PortInstance, PortCollection


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
        return handle

    def release(self):
        handle = self._current_handle
        if handle:
            handle.interrupt()


class ResourceContext:
    def __init__(self, resource: ResourceHandle):
        self._resource = resource

    def __enter__(self):
        return self._resource

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()

    def release(self):
        resource, self._resource = self._resource, None
        if resource:
            resource.release()

    def __bool__(self):
        return self._resource is not None

    @property
    def is_interrupted(self):
        if self._resource:
            return self._resource.is_interrupted
        else:
            return True


class Wrapper:
    def __init__(self, script, resource: ResourceWrapper):
        self._resource = resource
        self._script = script

    def sleep(self, s):
        self._script.sleep(s)

    def try_take_resource(self, callback=None):
        if self._script.is_stop_requested:
            raise InterruptedError

        return ResourceContext(self._resource.request(callback))

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
        'HC_SR04': Sensors.HC_SR04
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
        rgb = hex2rgb(color)

        for idx in leds:
            if not (1 <= idx <= self._ring_led.count):
                raise IndexError('Led index invalid: {}'.format(idx))
            self._user_leds[idx - 1] = rgb

        self.using_resource(partial(self._ring_led.display_user_frame, self._user_leds))


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
        self.log = lambda message: script.log("MotorPortWrapper[motor {}]: {}".format(motor.id, message))
        self._motor = motor

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
                    resource.run_uninterruptable(partial(self._motor.set_speed, 0))
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
        self.log = lambda message: script.log("DriveTrain: {}".format(message))
        self._drivetrain = drivetrain

        self.turn = wrap_async_method(self, drivetrain.turn)
        self.drive = wrap_async_method(self, drivetrain.drive)

    def set_speed(self, direction, speed, unit_speed=MotorConstants.UNIT_SPEED_RPM):
        self.log("set_speeds")

        resource = self.try_take_resource()
        if resource:
            try:
                self._drivetrain.set_speed(direction, speed, unit_speed)
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
            if self._script.is_stop_requested:
                raise InterruptedError

            # we already have the resource - check if it was taken away
            if self._res.is_interrupted:
                # need to release the stick before re-taking
                if sl == sr == 0:
                    self._res = None
            else:
                # the resource is ours, use it
                self._set_speeds(sl, sr)
        else:
            self._res = self.try_take_resource()
            if self._res:
                self.log("resource taken")
                self._set_speeds(sl, sr)

    def _set_speeds(self, sl, sr):
        try:
            self._drivetrain.set_speeds(sl, sr)
        finally:
            if sl == sr == 0:
                # manual stop: allow lower priority scripts to move
                self.log("resource released")
                self._res.release()


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

    def release_resources(self):
        for res in self._resources.values():
            res.release()

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

    def stop(self):
        pass

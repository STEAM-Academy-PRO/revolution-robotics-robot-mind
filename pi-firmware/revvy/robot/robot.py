from abc import abstractmethod
from functools import partial
from typing import Callable, NamedTuple

from revvy.hardware_dependent.sound import SoundControlV1, SoundControlV2
from revvy.mcu.rrrc_control import RevvyTransportBase
from revvy.robot.drivetrain import DifferentialDrivetrain
from revvy.robot.imu import IMU
from revvy.robot.led_ring import RingLed
from revvy.robot.ports.common import PortDriver, PortInstance
from revvy.robot.ports.motors.base import MotorPortHandler
from revvy.robot.ports.sensors.base import SensorPortHandler
from revvy.robot.sound import Sound
from revvy.robot.status import RobotStatusIndicator, RobotStatus
from revvy.robot.status_updater import McuStatusUpdater
from revvy.scripting.resource import Resource
from revvy.scripting.robot_interface import RobotInterface
from revvy.utils.logger import get_logger
from revvy.utils.stopwatch import Stopwatch
from revvy.utils.version import VERSION, Version
from revvy.scripting.variables import VariableSlot

SENSOR_ON_PORT_NOT_PRESENT = 0
SENSOR_ON_PORT_DISTANCE = 1
SENSOR_ON_PORT_BUTTON = 2
SENSOR_ON_PORT_INVALID = 3
SENSOR_ON_PORT_RGB = 4
SENSOR_ON_PORT_UNKNOWN = 0xFF


def to_sensor_type_index(expected_sensor):
    if expected_sensor == SENSOR_ON_PORT_BUTTON:
        return 1
    if expected_sensor == SENSOR_ON_PORT_DISTANCE:
        return 2
    if expected_sensor == SENSOR_ON_PORT_RGB:
        return 3
    return None


class BatteryStatus(NamedTuple):
    chargerStatus: int
    motor_battery_present: int
    main: int
    motor: int


def _default_bus_factory() -> RevvyTransportBase:
    from revvy.hardware_dependent.rrrc_transport_i2c import RevvyTransportI2C

    return RevvyTransportI2C(1)


# FIXME: why is this RobotInterface? The base class causes problems for the linter, and also doesn't seem to be necessary anywhere.
class Robot(RobotInterface):
    def __init__(self, bus_factory: Callable[[], RevvyTransportBase] = _default_bus_factory):
        self._bus_factory = bus_factory

        self._comm_interface = self._bus_factory()

        self._log = get_logger("Robot")

        self._script_variables = VariableSlot(4)

        self._robot_control = self._comm_interface.create_application_control()

        self._stopwatch = Stopwatch()

        setup = {
            Version("1.0"): SoundControlV1,
            Version("1.1"): SoundControlV1,
            Version("2.0"): SoundControlV2,
        }

        self._ring_led = RingLed(self._robot_control)
        self._sound = Sound(setup[VERSION.hw]())

        self._status = RobotStatusIndicator(self._robot_control)
        self._status_updater = McuStatusUpdater(self._robot_control)
        self._battery = BatteryStatus(chargerStatus=0, motor_battery_present=0, main=0, motor=0)

        self._imu = IMU()

        def _set_updater(slot_name, port: PortInstance[PortDriver], config):
            """Controls reading a port's status information from the MCU."""
            if config is None:
                self._status_updater.disable_slot(slot_name)
            else:
                self._status_updater.enable_slot(slot_name, port.driver.update_status)

        self._motor_ports = MotorPortHandler(self._robot_control)
        for port in self._motor_ports:
            port.on_config_changed.add(partial(_set_updater, f"motor_{port.id}"))

        self._sensor_ports = SensorPortHandler(self._robot_control)
        for port in self._sensor_ports:
            port.on_config_changed.add(partial(_set_updater, f"sensor_{port.id}"))

        self._drivetrain = DifferentialDrivetrain(self._robot_control, self._imu)

        self.update_status = self._status_updater.read
        self.ping = self._robot_control.ping

        self._resources = {
            "led_ring": Resource("RingLed"),
            "drivetrain": Resource("DriveTrain"),
            "sound": Resource("Sound"),
            **{f"motor_{port.id}": Resource(f"Motor {port.id}") for port in self._motor_ports},
            **{f"sensor_{port.id}": Resource(f"Sensor {port.id}") for port in self._sensor_ports},
        }

    @property
    def resources(self):
        return self._resources

    def __del__(self):
        self._comm_interface.close()

    @property
    def script_variables(self):
        return self._script_variables

    @property
    def robot_control(self):
        return self._robot_control

    @property
    def battery(self):
        return self._battery

    @property
    def imu(self):
        return self._imu

    @property
    def status(self):
        return self._status

    # TODO: these 2 return the wrong type? What was the intent?
    @property
    def motors(self) -> MotorPortHandler:
        return self._motor_ports

    @property
    def sensors(self) -> SensorPortHandler:
        return self._sensor_ports

    @property
    def drivetrain(self):
        return self._drivetrain

    @property
    def led(self):
        return self._ring_led

    @property
    def sound(self):
        return self._sound

    def play_tune(self, name):
        self._sound.play_tune(name)

    def time(self):
        return self._stopwatch.elapsed

    def __validate_one_sensor_port(self, sensor_idx, expected_type):
        port_type = to_sensor_type_index(expected_type)
        if port_type is None:
            return SENSOR_ON_PORT_UNKNOWN

        result = self._robot_control.test_sensor_on_port(sensor_idx + 1, port_type)

        if result.is_connected():
            return expected_type

        if result.is_not_connected():
            return SENSOR_ON_PORT_NOT_PRESENT

        if result.is_error():
            return SENSOR_ON_PORT_INVALID

        return SENSOR_ON_PORT_UNKNOWN

    def reset(self):
        self._log("reset()")
        self._ring_led.start_animation(RingLed.BreathingGreen)
        self._status_updater.reset()

        def _process_battery_slot(data):
            assert len(data) == 4
            main_status, main_percentage, motor_bat_present, motor_percentage = data

            self._battery = BatteryStatus(
                chargerStatus=main_status,
                motor_battery_present=motor_bat_present,
                main=main_percentage,
                motor=motor_percentage,
            )

        self._status_updater.enable_slot("battery", _process_battery_slot)
        self._status_updater.enable_slot("axl", self._imu.update_axl_data)
        self._status_updater.enable_slot("gyro", self._imu.update_gyro_data)
        self._status_updater.enable_slot("orientation", self._imu.update_orientation_data)
        self._status_updater.enable_slot("yaw", self._imu.update_yaw_angles)

        # TODO: do something useful with the reset signal
        self._status_updater.enable_slot("reset", lambda _: self._log("MCU reset detected"))

        self._drivetrain.reset()
        self._motor_ports.reset()
        self._sensor_ports.reset()
        self._sound.reset_volume()
        self._robot_control.orientation_reset()

        self._status.robot_status = RobotStatus.NotConfigured
        self._status.update()

    def stop(self):
        self._sound.wait()

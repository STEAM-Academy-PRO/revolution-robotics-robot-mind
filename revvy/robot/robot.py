# SPDX-License-Identifier: GPL-3.0-only

import os
import time

from revvy.hardware_dependent.rrrc_transport_i2c import RevvyTransportI2C
from revvy.hardware_dependent.sound import SoundControlV1, SoundControlV2
from revvy.mcu.commands import BatteryStatus
from revvy.mcu.rrrc_control import RevvyControl, BootloaderControl
from revvy.robot.configurations import Motors, Sensors
from revvy.robot.drivetrain import DifferentialDrivetrain
from revvy.robot.imu import IMU
from revvy.robot.led_ring import RingLed
from revvy.robot.ports.common import PortInstance
from revvy.robot.ports.motor import create_motor_port_handler
from revvy.robot.ports.sensor import create_sensor_port_handler
from revvy.robot.sound import Sound
from revvy.robot.status import RobotStatusIndicator, RobotStatus
from revvy.robot.status_updater import McuStatusUpdater
from revvy.utils.assets import Assets
from revvy.utils.logger import get_logger
from revvy.utils.version import Version


class Robot:
    BOOTLOADER_I2C_ADDRESS = 0x2B
    ROBOT_I2C_ADDRESS = 0x2D

    def __init__(self, i2c_bus=1):
        self._i2c_bus = i2c_bus

        self._assets = Assets()
        self._assets.add_source(os.path.join('data', 'assets'))

        self._log = get_logger('Robot')

    def __enter__(self):
        self._i2c = RevvyTransportI2C(self._i2c_bus)

        self._robot_control = RevvyControl(self._i2c.bind(self.ROBOT_I2C_ADDRESS))
        self._bootloader_control = BootloaderControl(self._i2c.bind(self.BOOTLOADER_I2C_ADDRESS))

        self._start_time = time.time()

        # read versions
        self._hw_version = self._robot_control.get_hardware_version()
        self._fw_version = self._robot_control.get_firmware_version()

        self._log('Hardware: {}\nFirmware: {}'.format(self._hw_version, self._fw_version))

        setup = {
            Version('1.0'): SoundControlV1,
            Version('1.1'): SoundControlV1,
            Version('2.0'): SoundControlV2,
        }

        self._ring_led = RingLed(self._robot_control)
        self._sound = Sound(setup[self._hw_version](), self._assets.category_loader('sounds'))

        self._status = RobotStatusIndicator(self._robot_control)
        self._status_updater = McuStatusUpdater(self._robot_control)
        self._battery = BatteryStatus(0, 0, 0)

        self._imu = IMU()

        def _motor_config_changed(motor: PortInstance, config_name):
            callback = None if config_name == 'NotConfigured' else motor.update_status
            self._status_updater.set_slot('motor_{}'.format(motor.id), callback)

        def _sensor_config_changed(sensor: PortInstance, config_name):
            callback = None if config_name == 'NotConfigured' else sensor.update_status
            self._status_updater.set_slot('sensor_{}'.format(sensor.id), callback)

        self._motor_ports = create_motor_port_handler(self._robot_control, Motors)
        for port in self._motor_ports:
            port.on_config_changed(_motor_config_changed)

        self._sensor_ports = create_sensor_port_handler(self._robot_control, Sensors)
        for port in self._sensor_ports:
            port.on_config_changed(_sensor_config_changed)

        self._drivetrain = DifferentialDrivetrain(self._robot_control, self._motor_ports.port_count)

        self.update_status = self._status_updater.read
        self.ping = self._robot_control.ping

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._i2c.close()

    @property
    def assets(self):
        return self._assets

    @property
    def robot_control(self):
        return self._robot_control

    @property
    def bootloader_control(self):
        return self._bootloader_control

    @property
    def start_time(self):
        return self._start_time

    @property
    def hw_version(self) -> Version:
        return self._hw_version

    @property
    def fw_version(self) -> Version:
        return self._fw_version

    @property
    def battery(self):
        return self._battery

    @property
    def imu(self):
        return self._imu

    @property
    def status(self):
        return self._status

    @property
    def motors(self):
        return self._motor_ports

    @property
    def sensors(self):
        return self._sensor_ports

    @property
    def drivetrain(self):
        return self._drivetrain

    @property
    def led_ring(self):
        return self._ring_led

    @property
    def sound(self):
        return self._sound

    def reset(self):
        self._log('reset()')
        self._ring_led.set_scenario(RingLed.BreathingGreen)
        self._status_updater.reset()

        def _process_battery_slot(data):
            assert len(data) == 4
            main_status = data[0]
            main_percentage = data[1]
            # motor_status = data[2]
            motor_percentage = data[3]

            self._battery = BatteryStatus(chargerStatus=main_status, main=main_percentage, motor=motor_percentage)

        self._status_updater.set_slot("battery", _process_battery_slot)
        self._status_updater.set_slot("axl", self._imu.update_axl_data)
        self._status_updater.set_slot("gyro", self._imu.update_gyro_data)
        self._status_updater.set_slot("yaw", self._imu.update_yaw_angles)
        # TODO: do something useful with the reset signal
        self._status_updater.set_slot("reset", lambda x: self._log('MCU reset detected'))

        self._drivetrain.reset()
        self._motor_ports.reset()
        self._sensor_ports.reset()

        self._status.robot_status = RobotStatus.NotConfigured
        self._status.update()

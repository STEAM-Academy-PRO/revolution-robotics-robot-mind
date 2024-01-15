# SPDX-License-Identifier: GPL-3.0-only

import enum
import os
import signal
import traceback
import time
from functools import partial
from threading import Event

from revvy.mcu.rrrc_transport import TransportException
from revvy.robot.robot import Robot
from revvy.robot.remote_controller import RemoteController, RemoteControllerScheduler, create_remote_controller_thread
from revvy.robot.led_ring import RingLed
from revvy.robot.status import RobotStatus, RemoteControllerStatus
from revvy.robot_config import empty_robot_config
from revvy.scripting.resource import Resource
from revvy.scripting.robot_interface import MotorConstants
from revvy.scripting.runtime import ScriptManager
from revvy.utils.logger import get_logger
from revvy.utils.stopwatch import Stopwatch
from revvy.utils.thread_wrapper import periodic
from revvy.robot.communication import RobotCommunicationInterface


class RevvyStatusCode(enum.IntEnum):
    OK = 0
    ERROR = 1
    INTEGRITY_ERROR = 2
    UPDATE_REQUEST = 3


class RobotManager:
    def __init__(self, robot: Robot, sw_version):
        self._log = get_logger('RobotManager')
        self._log('init')
        self.needs_interrupting = True

        self._configuring = False
        self._robot = robot
        self._sw_version = sw_version
        self.need_print = 1

        self._status_update_thread = periodic(self._update, 0.005, "RobotStatusUpdaterThread")
        self._background_fns = []

        rc = RemoteController()
        rcs = RemoteControllerScheduler(rc)
        rcs.on_controller_detected(self._on_controller_detected)
        rcs.on_controller_lost(self._on_controller_lost)
        self._remote_controller_scheduler = rcs

        self._remote_controller = rc
        self._remote_controller_thread = create_remote_controller_thread(rcs)

        self._resources = {
            'led_ring':   Resource('RingLed'),
            'drivetrain': Resource('DriveTrain'),
            'sound':      Resource('Sound'),

            **{f'motor_{port.id}': Resource(f'Motor {port.id}') for port in self._robot.motors},
            **{f'sensor_{port.id}': Resource(f'Sensor {port.id}') for port in self._robot.sensors}
        }

        self._scripts = ScriptManager(self)
        self._bg_controlled_scripts = ScriptManager(self)
        self._autonomous = 0
        self._config = empty_robot_config

        self._status_code = RevvyStatusCode.OK
        self.exited = Event()

        self.start_remote_controller = self._remote_controller_thread.start
        self.__session_id = 0

    def set_control_interface_callbacks(self, robot_interface: RobotCommunicationInterface):
        self._robot_interface = robot_interface

        self._robot_interface.update_session_id(0xffffffff)
        self._robot_interface.set_periodic_control_msg_cb(self._remote_controller_scheduler.data_ready)
        self._robot_interface.set_joystick_action_cb(self._remote_controller.on_joystick_action)
        self._robot_interface.set_validate_config_req_cb(self.__on_validate_config_requested)
        self._robot_interface.on_connection_changed(self._on_connection_changed)

        self._robot.set_validate_config_done_cb(self._robot_interface.set_validation_result)

    def __on_validate_config_requested(self, motors, sensors, motor_load_power,
        threshold):
        self.run_in_background(partial(self._robot.validate_config, motors,
            sensors, motor_load_power, threshold))
        print('Validation request: motors={}, sensors={},pwr:{},sen:{}'.format(
            motors, sensors, motor_load_power, threshold))


    def process_run_in_bg_requests(self):
        functions = self._background_fns
        self._background_fns = []
        for i, f in enumerate(functions):
            self._log(f'Running {i}/{len(functions)} background functions')
            f()

    def process_autonomous_requests(self):
        if self._autonomous == 'ready':
            req = self.remote_controller.fetch_autonomous_requests()
            if req.is_start_pending():
                self._bg_controlled_scripts.start_all_scripts()
            elif req.is_pause_pending():
                self._bg_controlled_scripts.pause_all_scripts()
            elif req.is_stop_pending():
                self._bg_controlled_scripts.stop_all_scripts()
            elif req.is_resume_pending():
                self._bg_controlled_scripts.resume_all_scripts()

    def __battery_characterstic(self, name):
        return self._robot_interface.battery(name)


    def _update(self):
        # noinspection PyBroadException
        try:
            self._robot.update_status()

            self.__battery_characterstic('main_battery').update_value(
                self._robot.battery.main)

            self.__battery_characterstic('motor_battery').update_value(
                self._robot.battery.motor)

            self.__battery_characterstic('unified_battery_status').update_value(
              self._robot.battery.main,
              self._robot.battery.chargerStatus,
              self._robot.battery.motor,
              self._robot.battery.motor_battery_present)

            self._remote_controller.timer_increment()
            vector_list = [
                getattr(self._robot.imu.rotation, 'x'),
                getattr(self._robot.imu.rotation, 'y'),
                getattr(self._robot.imu.rotation, 'z'),
            ]
            vector_orientation = [
                getattr(self._robot.imu.orientation, 'pitch'),
                getattr(self._robot.imu.orientation, 'roll'),
                getattr(self._robot.imu.orientation, 'yaw'),
            ]
            self._robot_interface.update_orientation(vector_orientation)
            self._robot_interface.update_gyro(vector_list)
            self._robot_interface.update_script_variable(self._robot.script_variables)
            self._robot_interface.update_state_control(self.remote_controller.background_control_state)

            self._robot_interface.update_timer(self._remote_controller.processing_time)

            if self.need_print:
                self.need_print = 0

            self.process_run_in_bg_requests()
            self.process_autonomous_requests()

        except TransportException:
            self._log(traceback.format_exc())
            self.exit(RevvyStatusCode.ERROR)
        except Exception:
            self._log(traceback.format_exc())

    @property
    def resources(self):
        return self._resources

    @property
    def config(self):
        return self._config

    @property
    def status_code(self):
        return self._status_code

    @property
    def robot(self):
        return self._robot

    @property
    def remote_controller(self):
        return self._remote_controller

    def exit(self, status_code):
        self._log(f'exit requested with code {status_code}')
        self._status_code = status_code
        if self.needs_interrupting:
            os.kill(os.getpid(), signal.SIGINT)
        self.exited.set()

    def wait_for_exit(self):
        self.exited.wait()
        return self._status_code

    def request_update(self):
        def update():
            self._log('Exiting to update')
            time.sleep(1)
            self.exit(RevvyStatusCode.UPDATE_REQUEST)

        self.run_in_background(update)

    def robot_start(self):
        self._log('start')
        if self._robot.status.robot_status == RobotStatus.StartingUp:
            self._log('Waiting for MCU')

            try:
                self._ping_robot()
            except TimeoutError:
                pass  # FIXME somehow handle a dead MCU

            self._robot_interface.update_characteristic('hw_version', str(self._robot.hw_version))
            self._robot_interface.update_characteristic('fw_version', str(self._robot.fw_version))
            self._robot_interface.update_characteristic('sw_version', str(self._sw_version))

            # start reader thread
            self._status_update_thread.start()

            # self._robot_interface.start()

            self._robot.status.robot_status = RobotStatus.NotConfigured
            self.robot_configure(None, partial(self._robot.play_tune, 'robot2'))

    def run_in_background(self, callback):
        if callable(callback):
            self._log('Registering new background function')
            self._background_fns.append(callback)
        else:
            raise ValueError('callback is not callable')

    def _on_connection_changed(self, is_connected):
        self._log('Phone connected' if is_connected else 'Phone disconnected')
        if not is_connected:
            self._robot.status.controller_status = RemoteControllerStatus.NotConnected
            self._robot.play_tune('disconnect')
            self.robot_configure(None)
        else:
            self._robot.status.controller_status = RemoteControllerStatus.ConnectedNoControl
            self._robot.play_tune('bell')

    def _on_controller_detected(self):
        self._log('Remote controller detected')
        self._robot.status.controller_status = RemoteControllerStatus.Controlled

    def _on_controller_lost(self):
        self._robot_interface.update_session_id(0)
        self._log('Remote controller lost')
        if self._robot.status.controller_status != RemoteControllerStatus.NotConnected:
            self._robot.status.controller_status = RemoteControllerStatus.ConnectedNoControl
            self.robot_configure(None)

    def robot_configure(self, config, after=None):
        self.__session_id += 1
        self._log('Request configuration')
        if config is not None:
            self._robot_interface.update_session_id(self.__session_id)

        if self._robot.status.robot_status != RobotStatus.Stopped:
            self.run_in_background(partial(self._robot_configure, config))
            if callable(after):
                self.run_in_background(after)

    def _reset_configuration(self):
        for scr in [self._scripts, self._bg_controlled_scripts]:
            scr.reset()
            scr.assign('Motor', MotorConstants)
            scr.assign('RingLed', RingLed)

        self._remote_controller_thread.stop().wait()

        for res in self._resources.values():
            res.reset()

        # ping robot, because robot may reset after stopping scripts
        self._ping_robot()

        self._robot.reset()

    def _apply_new_configuration(self, config):
        self._log('Applying new configuration')
        self._robot.script_variables.reset()

        # Initialize variable slots from config
        scriptvars = []
        for varconf in config.controller.variable_slots:
            slot_idx =  varconf['slot']
            v = self._robot.script_variables.get_variable(slot_idx)
            v.init(varconf['script'], varconf['variable'], 0.0)
            scriptvars.append(v)

        self._bg_controlled_scripts.assign('list_slots', scriptvars)

        # set up motors
        for motor in self._robot.motors:
            motor.configure(config.motors[motor.id])
            motor.on_status_changed.add(lambda p: self._robot_interface.update_motor(p.id, p.power, p.speed, p.pos))

        for motor_id in config.drivetrain['left']:
            self._robot.drivetrain.add_left_motor(self._robot.motors[motor_id])

        for motor_id in config.drivetrain['right']:
            self._robot.drivetrain.add_right_motor(self._robot.motors[motor_id])

        # set up sensors
        for sensor in self._robot.sensors:
            sensor.configure(config.sensors[sensor.id])
            sensor.on_status_changed.add(lambda p: self._robot_interface.update_sensor(p.id, p.raw_value))

        def start_analog_script(src, channels):
            src.start(channels=channels)

        # set up remote controller
        for analog in config.controller.analog:
            script_handle = self._scripts.add_script(analog['script'])
            self._remote_controller.on_analog_values(analog['channels'], partial(start_analog_script, script_handle))

        for button, script in enumerate(config.controller.buttons):
            if script:
                script_handle = self._scripts.add_script(script)
                script_handle.assign('list_slots', scriptvars)
                self._remote_controller.on_button_pressed(button, script_handle.start)

        self._autonomous = config.background_initial_state

        for script in config.background_scripts:
            self._bg_controlled_scripts.add_script(script)

        self.remote_controller.reset_background_control_state()
        if config.background_initial_state == 'running':
            self._bg_controlled_scripts.start_all_scripts()

    def _robot_configure(self, config):

        is_default_config = not config and self._robot.status.robot_status != RobotStatus.Stopped

        if is_default_config:
            config = empty_robot_config

        self._config = config

        self._scripts.stop_all_scripts()
        self._reset_configuration()

        self._apply_new_configuration(config)
        if is_default_config:
            self._log('Default configuration applied')
            self._robot.status.robot_status = RobotStatus.NotConfigured
        else:
            self._robot.status.robot_status = RobotStatus.Configured

    def robot_stop(self):
        self._robot.status.controller_status = RemoteControllerStatus.NotConnected
        self._robot.status.robot_status = RobotStatus.Stopped
        self._remote_controller_thread.exit()
        self._robot_interface.stop()
        self._scripts.reset()
        self._status_update_thread.exit()
        self._robot.stop()

    def _ping_robot(self, timeout=0):
        stopwatch = Stopwatch()
        retry_ping = True
        while retry_ping:
            retry_ping = False
            try:
                self._robot.ping()
            except (BrokenPipeError, IOError, OSError):
                retry_ping = True
                time.sleep(0.1)
                if timeout != 0 and stopwatch.elapsed > timeout:
                    raise TimeoutError

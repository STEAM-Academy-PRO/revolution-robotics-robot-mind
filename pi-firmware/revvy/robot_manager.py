
import enum
import os
import signal
import traceback
import time
from functools import partial
from threading import Event

from revvy.mcu.rrrc_transport import TransportException
from revvy.robot.communication import RobotCommunicationInterface
from revvy.robot.robot import Robot
from revvy.robot.remote_controller import RemoteController, RemoteControllerScheduler, create_remote_controller_thread
from revvy.robot.led_ring import RingLed
from revvy.robot.status import RobotStatus, RemoteControllerStatus
from revvy.robot_config import empty_robot_config
from revvy.scripting.robot_interface import MotorConstants
from revvy.scripting.runtime import ScriptEvent, ScriptHandle, ScriptManager
from revvy.utils.directories import WRITEABLE_ASSETS_DIR
from revvy.utils.logger import LogLevel, get_logger
from revvy.utils.stopwatch import Stopwatch
from revvy.utils.thread_wrapper import periodic

class RevvyStatusCode(enum.IntEnum):
    """ Exit codes we used to tell the loader what happened """

    # Manual exit. The loader will exit, too. Exiting with OK only makes sense if the package is
    # not managed by the revvy.service.
    OK = 0

    # An error has occurred. The loader is allowed to reload this package
    ERROR = 1

    # The loader should try to load a previous package
    INTEGRITY_ERROR = 2

    # The loader should try to install and load a new package
    UPDATE_REQUEST = 3


class RobotManager:
    def __init__(self):
        self._log = get_logger('RobotManager')
        self.needs_interrupting = True

        self._configuring = False
        self._robot = Robot()
        self._robot.assets.add_source(WRITEABLE_ASSETS_DIR)

        self._status_update_thread = periodic(self._update, 0.005, "RobotStatusUpdaterThread")
        self._background_fns = []

        rc = RemoteController()
        rcs = RemoteControllerScheduler(rc)
        rcs.on_controller_detected(self._on_controller_detected)
        rcs.on_controller_lost(self._on_controller_lost)
        self._remote_controller_scheduler = rcs

        self._remote_controller = rc
        self._remote_controller_thread = create_remote_controller_thread(rcs)

        self._scripts = ScriptManager(self._robot)
        self._bg_controlled_scripts = ScriptManager(self._robot)
        self._autonomous = 0
        self._config = empty_robot_config

        self._status_code = RevvyStatusCode.OK
        self.exited = Event()

        self.start_remote_controller = self._remote_controller_thread.start
        self.__session_id = 0

        self.on_joystick_action = self._remote_controller.on_joystick_action

        self.handle_periodic_control_message = self._remote_controller_scheduler.periodic_control_message_handler

        self._robot_interface = None

    def set_communication_interface_callbacks(self, communication_interface: RobotCommunicationInterface):
        # Ditch former connection!
        if self._robot_interface is not None:
            self._robot_interface.disconnect()
        self._robot_interface = communication_interface

    def validate_config_async(self, motors, sensors, motor_load_power,
        threshold, callback):
        self.run_in_background(partial(self.validate_config, motors,
            sensors, motor_load_power, threshold, callback), '__on_validate_config_requested')

        self._log('Validation request: motors={}, sensors={},pwr:{},sen:{}'.format(
            motors, sensors, motor_load_power, threshold))


    def validate_config(self, motors, sensors, motor_load_power, threshold, callback):
        self._log('validate req: motors={}, sensors={},pwr:{},sen:{}'.format(
            motors, sensors, motor_load_power, threshold))

        success = True
        motors_result = []
        for motor_port_idx, should_check_port in enumerate(motors):
            motor_port_num = motor_port_idx + 1
            self._log(f'checking motor at port "M{motor_port_num}"')
            motor_is_present = False
            if not motor_load_power:
                motor_load_power = 60
            if not threshold:
                threshold = 10
            if should_check_port:
                motor_is_present = self._robot._robot_control.test_motor_on_port(
                    motor_port_num, motor_load_power, threshold)

            status_string = 'unchecked'
            if motor_is_present:
                status_string = 'attached'
            elif should_check_port:
                status_string = 'detached'

            self._log('Motor port "M{} check result:{}'.format(motor_port_num,
                status_string))

            motors_result.append(motor_is_present)

        sensors_result = []
        for sensor_idx, sensor_expected_type in enumerate(sensors):
            tested_type = self._robot.__validate_one_sensor_port(sensor_idx,
                sensor_expected_type)
            sensors_result.append(tested_type)

        callback(success, motors_result, sensors_result)

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


    def _update(self):
        """
            This runs every 5ms and reads out the robot's statuses.
        """
        # noinspection PyBroadException
        try:
            self._robot.update_status()

            self._robot_interface.update_battery(
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

            self.process_run_in_bg_requests()
            self.process_autonomous_requests()

        except TransportException:
            self._log(traceback.format_exc())
            self.exit(RevvyStatusCode.ERROR)
        except BrokenPipeError:
            self._log("Status Update Error from MCU", LogLevel.WARNING)
        except OSError as e:
            self._log(f"{str(e)}", LogLevel.WARNING)
        except Exception:
            self._log(traceback.format_exc())



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

        self.run_in_background(update, 'updater')

    def robot_start(self):
        self._log('start')
        if self._robot.status.robot_status == RobotStatus.StartingUp:
            self._log('Waiting for MCU')

            try:
                self._ping_robot()
            except TimeoutError:
                pass  # FIXME somehow handle a dead MCU

            self._log('Connection to MCU established')

            # start reader thread
            self._status_update_thread.start()

            self._robot.status.robot_status = RobotStatus.NotConfigured

            # Initial robot reset.

            def boot_up_success():
                self._robot.play_tune('robot2')
                self._log('robot first configured with empty configuration object!')

            self.robot_configure(None, boot_up_success)

    def run_in_background(self, callback, name=''):
        if callable(callback):
            self._log(f'Registering new background function {name}')
            self._background_fns.append(callback)
        else:
            raise ValueError('callback is not callable')

    def on_connection_changed(self, is_connected):
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
        if config is not None:
            self._robot_interface.update_session_id(self.__session_id)

        if self._robot.status.robot_status != RobotStatus.Stopped:
            self.run_in_background(partial(self._robot_configure, config), 'robot_configuration_request')
            if callable(after):
                traceback.print_exc()
                self.run_in_background(after, 'robot_configuration_request - 2')

    def _reset_configuration(self):
        for scr in [self._scripts, self._bg_controlled_scripts]:
            scr.reset()
            scr.assign('Motor', MotorConstants)
            scr.assign('RingLed', RingLed)

        self._remote_controller_thread.stop().wait()

        for res in self._robot._resources.values():
            res.reset()

        # ping robot, because robot may reset after stopping scripts
        self._ping_robot()

        self._robot.reset()

    def _apply_new_configuration(self, config):
        # self._log('Applying new configuration')
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
            script_handle = self._scripts.add_script(analog['script'], config)
            self._remote_controller.on_analog_values(analog['channels'], partial(start_analog_script, script_handle))

        # Set up all the bound buttons to run the stored scripts.
        for button, script in enumerate(config.controller.buttons):
            if script:
                script_handle = self._scripts.add_script(script, config)
                script_handle.assign('list_slots', scriptvars)
                self._remote_controller.link_button_to_runner(button, script_handle)

                script_handle.on(ScriptEvent.START, self._on_script_running)
                script_handle.on(ScriptEvent.STOP, self._on_script_stopped)
                script_handle.on(ScriptEvent.ERROR, self._on_script_error)

        self._autonomous = config.background_initial_state

        for script in config.background_scripts:
            bg_script_handle = self._bg_controlled_scripts.add_script(script, config)

            # For background scripts, now we do not send up program running states, as
            # they are not actually buttons to be bound to. We need to re-think the configuration
            # object as right now we do not have a good way to ID the running programs, other than
            # having their button bound ID. This is a poor design choice, as it interferes with
            # background programs. Until then, we do not track the state of background programs
            # in here.
            # IF I dug it out right, currently we actually have ONE state for
            # ALL the background processes communicated in another BLE characteristic.
            # I did not touch that for now, but this yells for some legwork in design.
            bg_script_handle.on(ScriptEvent.START,
                        lambda ref, data: self._on_script_running(ref, None, send_status=False))
            bg_script_handle.on(ScriptEvent.STOP,
                        lambda ref, data:  self._on_script_stopped(ref, None, send_status=False))
            bg_script_handle.on(ScriptEvent.ERROR,
                        lambda ref, error: self._on_script_error(ref, error, send_status=False))

        self.remote_controller.reset_background_control_state()
        if config.background_initial_state == 'running':
            self._bg_controlled_scripts.start_all_scripts()


    def _on_script_running(self, script_handle: ScriptHandle, data=None, send_status=True):
        """ When script started, notify phone app. """
        if send_status:
            self._robot_interface.update_program_status(script_handle.descriptor.ref_id, ScriptEvent.START)

    def _on_script_error(self, script_handle: ScriptHandle, exception, send_status=True):
        """
            Handle runner script errors gracefully, and type out what caused it to bail!
            These are user scripts, so we should consider sending them back via Bluetooth
        """
        self._log(f'ERROR in userscript: {script_handle.descriptor.name}', LogLevel.ERROR)
        self._log(f'ERROR:  {str(exception)}', LogLevel.ERROR)
        self._log(f'Source that caused the error: \n\n{script_handle.descriptor.source}\n\n', LogLevel.ERROR)
        self._log(f'{traceback.format_exc()}', LogLevel.ERROR)
        if send_status:
            self._robot_interface.update_program_status(script_handle.descriptor.ref_id, ScriptEvent.ERROR)

        # On code execution error, do send visible signals to the user about the code being broken.
        self._robot.led.start_animation(RingLed.Bug)
        self._robot.sound.play_tune('uh_oh')
        time.sleep(1)
        self._robot.led.start_animation(RingLed.Off)

    def _on_script_stopped(self, script_handle: ScriptHandle, data=None, send_status=True):
        """ If we want to send back script status stopped change, this is the place. """
        # self._log(f'script: {script.name}')
        if send_status:
            self._robot_interface.update_program_status(script_handle.descriptor.ref_id, ScriptEvent.STOP)

    def _robot_configure(self, config):

        is_default_config = not config and self._robot.status.robot_status != RobotStatus.Stopped

        if is_default_config:
            config = empty_robot_config

        self._config = config

        self._scripts.stop_all_scripts()
        self._reset_configuration()

        self._apply_new_configuration(config)
        if is_default_config:
            # self._log('Default configuration applied')
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

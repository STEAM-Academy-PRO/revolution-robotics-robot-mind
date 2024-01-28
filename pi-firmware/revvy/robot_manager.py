"""
    Manages robot on high level.
    Instantiates Robot, RemoteController, preserves state,
    processes configuration messages.
"""

import enum
import os
import signal
import traceback
import time
from functools import partial
from threading import Event

from revvy.robot.robot import Robot
from revvy.robot.remote_controller import RemoteController, RemoteControllerScheduler
from revvy.robot.remote_controller import create_remote_controller_thread
from revvy.robot.led_ring import RingLed
from revvy.robot.robot_events import MotorChangeData, RobotEvent
from revvy.robot.robot_state import RobotState
from revvy.robot.states.sensor_states import create_sensor_data_wrapper
from revvy.robot.status import RobotStatus, RemoteControllerStatus
from revvy.robot_config import empty_robot_config
from revvy.scripting.robot_interface import MotorConstants
from revvy.scripting.runtime import ScriptEvent, ScriptHandle, ScriptManager
from revvy.utils.logger import LogLevel, get_logger
from revvy.utils.stopwatch import Stopwatch


class RevvyStatusCode(enum.IntEnum):
    OK = 0
    ERROR = 1
    INTEGRITY_ERROR = 2
    UPDATE_REQUEST = 3


class RobotManager:
    """ High level class to manage robot state and configuration """
    def __init__(self):
        self._log = get_logger('RobotManager')
        self.needs_interrupting = True

        self._configuring = False
        self._robot = Robot()

        self._background_fns = []

        rc = RemoteController()
        rcs = RemoteControllerScheduler(rc)
        rcs.on_controller_detected(self._on_controller_detected)
        rcs.on_controller_lost(self._on_controller_lost)
        self._remote_controller_scheduler = rcs

        self._connected_device_name = ''

        self._remote_controller = rc
        self._remote_controller_thread = create_remote_controller_thread(rcs)

        self._robot_state = RobotState(self._robot, self._remote_controller)

        self._scripts = ScriptManager(self._robot)
        self._bg_controlled_scripts = ScriptManager(self._robot)
        self._autonomous = 0
        self._config = empty_robot_config

        self._status_code = RevvyStatusCode.OK
        self.exited = Event()

        self.__session_id = 0

        self.on_joystick_action = self._remote_controller.on_joystick_action

        self.handle_periodic_control_message = self._remote_controller_scheduler.periodic_control_message_handler

        self._robot_state.on(RobotEvent.FATAL_ERROR, self.exit)

        # Start reading status from the robot.
        self._robot_state.start_polling_mcu()

        # TODO: REMOVE THIS
        self._robot_interface = None

        self.on = self._robot_state.on
        self.trigger = self._robot_state.trigger

        # TODO: This is temporary until I figure out WHY we need to run this every 5ms
        self.on(RobotEvent.MCU_TICK, self.process_run_in_bg_requests)
        self.on(RobotEvent.MCU_TICK, self.process_autonomous_requests)

    # @ deprecated!
    # def set_communication_interface_callbacks(self, communication_interface: RobotCommunicationInterface):
    #     # Ditch former connection!
    #     if self._robot_interface is not None:
    #         self._robot_interface.disconnect()
    #     self._robot_interface = communication_interface

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



    # Why is this in here, and not e.g. in the control message handler?
    # This was triggered every 5, i repeat, EVERY FIVE MILLISECONDS!!!?!?
    # WHYYYY?

    def process_run_in_bg_requests(self):
        functions = self._background_fns
        self._background_fns = []
        for i, f in enumerate(functions):
            self._log(f'Running {i}/{len(functions)} background functions')
            f()

    # So as this.

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

    def on_connected(self, device_name):
        """ When interface connects """
        self._connected_device_name = device_name
        self._log(f"{device_name} device connected!")
        self._robot.status.controller_status = RemoteControllerStatus.ConnectedNoControl
        self._robot.play_tune('bell')

    def on_disconnected(self):
        """ Reset, play tune """
        self._log(f"Device disconnected: {self._connected_device_name}")
        self._robot.status.controller_status = RemoteControllerStatus.NotConnected
        self._robot.play_tune('disconnect')
        self.robot_configure(None)


    def on_connection_changed(self, is_connected):
        self._log('Phone connected' if is_connected else 'Phone disconnected')

    def _on_controller_detected(self):
        self._log('Remote controller detected')
        self._robot.status.controller_status = RemoteControllerStatus.Controlled

    def _on_controller_lost(self):
        self._log('Remote controller lost')
        if self._robot.status.controller_status != RemoteControllerStatus.NotConnected:
            self._robot.status.controller_status = RemoteControllerStatus.ConnectedNoControl
            self.robot_configure(None)
            self.reset_configuration()


    def reset_configuration(self):
        """ When RC disconnects """
        self._robot.status.robot_status = RobotStatus.NotConfigured
        self._remote_controller_thread.stop()
        self._scripts.stop_all_scripts()
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

    def robot_configure(self, config, call_when_done=None):
        """
            Set the robot ports to the proper state defined in config
            then start RemoteController.
        """
        self.__session_id += 1
        self.trigger(RobotEvent.SESSION_ID_CHANGE, self.__session_id)
        self._log(f"New Configuration with session ID: {self.__session_id}")

        self._config = config

        # Start with resetting everything.
        self.reset_configuration()

        self._apply_new_configuration(config)

        self._robot.status.robot_status = RobotStatus.Configured

        # You would assume reset does what it says... No you'd have to call reset
        # even after config.
        self._robot.reset()

        self._remote_controller_thread.start()
        ### This used to be called in a background process, I have no clue why, but I am removing it.
        # if self._robot.status.robot_status != RobotStatus.Stopped:
            # self.run_in_background(partial(self._robot_configure, config), 'robot_configuration_request')
        if callable(call_when_done):
            # traceback.print_exc()
            call_when_done()
            # self.run_in_background(call_when_done, 'robot_configuration_request - 2')


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
            ### TODO! ---------------------------------------------------------------------------------
            motor.on_status_changed.add(lambda p:
                            self.trigger(RobotEvent, MotorChangeData(p.id, p.power, p.speed, p.pos)))

        for motor_id in config.drivetrain['left']:
            self._robot.drivetrain.add_left_motor(self._robot.motors[motor_id])

        for motor_id in config.drivetrain['right']:
            self._robot.drivetrain.add_right_motor(self._robot.motors[motor_id])

        # set up sensors
        for sensor_port in self._robot.sensors:
            self._log(f'Configuring sensor {sensor_port.id} {config.sensors[sensor_port.id]}')
            # Code smell: Instead of creating a new sensor object, we just
            # configure one. I'd prefer re-initializing the Sensor object.
            # not sure if it ditches the references.

            # Some of this is defined in the config parser some in the sensor code
            # making it pretty hard to debug.
            # It links the types IN the config already, super hard to figure out where
            # the actual sending down to MCU happens. I want to believe that there is a reason
            # but loosing hope.
            # sensor_port is actually a port_instance, but how it actually changes the behavior
            # is a huge black hole.
            # I would prefer to create SensorPort classes in here, the configuration part, handle
            # the emitting, data-cleaning, event-smoothening/throttling and everything under one roof
            # because it DEPENDS what kind of a sensor it is how to clean the signal.

            sensor_config = config.sensors[sensor_port.id]

            sensor_port.configure(sensor_config)

            create_sensor_data_wrapper(sensor_port, sensor_config, lambda event_data:
                                         self.trigger(RobotEvent.SENSOR_VALUE_CHANGE, event_data))

            # Also, I'd love to see all the robot status changes WITHIN the robot in one place,
            # most probably in the robot object.
            # sensor_port.on_status_changed.add(lambda p:
                                        #  self.trigger(RobotEvent.SENSOR_VALUE_CHANGE, SensorEventData(p.id, p.raw_value)))

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

                script_handle.on(ScriptEvent.STOP, self._on_script_stopped)
                script_handle.on(ScriptEvent.ERROR, self._on_script_error)

        self._autonomous = config.background_initial_state

        for script in config.background_scripts:
            self._bg_controlled_scripts.add_script(script, config)

        self.remote_controller.reset_background_control_state()
        if config.background_initial_state == 'running':
            self._bg_controlled_scripts.start_all_scripts()


    def _on_script_error(self, script: ScriptHandle, ex):
        """
            Handle runner script errors gracefully, and type out what caused it to bail!
            These are user scripts, so we should consider sending them back via Bluetooth
        """
        self._log(f'ERROR in userscript: {script.name}', LogLevel.ERROR)
        self._log(f'ERROR:  {str(ex)}', LogLevel.ERROR)
        self._log(f'Source that caused the error: \n\n{script.descriptor.source}\n\n', LogLevel.ERROR)
        self._log(f'{traceback.format_exc()}', LogLevel.ERROR)

    def _on_script_stopped(self, script, data=None):
        """ If we want to send back script status stopped change, this is the place. """
        # self._log(f'script: {script.name}')
        pass

    # def _robot_configure(self, config):



    def robot_stop(self, *args):
        """ On exiting let's reset all states. """
        self._robot_state.stop_polling_mcu()
        self._robot.status.controller_status = RemoteControllerStatus.NotConnected
        self._robot.status.robot_status = RobotStatus.Stopped
        self._remote_controller_thread.exit()
        self.trigger(RobotEvent.STOPPED)
        self._scripts.reset()
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

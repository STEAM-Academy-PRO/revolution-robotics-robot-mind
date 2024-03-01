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
from revvy.robot.remote_controller import (
    AutonomousModeRequest,
    RemoteController,
    RemoteControllerCommand,
    RemoteControllerScheduler,
)
from revvy.robot.remote_controller import create_remote_controller_thread
from revvy.robot.led_ring import RingLed
from revvy.robot.robot_events import ProgramStatusChange, RobotEvent
from revvy.robot.robot_state import RobotState
from revvy.robot.states.sensor_states import create_sensor_data_wrapper
from revvy.robot.status import RobotStatus, RemoteControllerStatus
from revvy.robot_config import empty_robot_config
from revvy.scripting.robot_interface import MotorConstants
from revvy.scripting.runtime import ScriptEvent, ScriptHandle, ScriptManager
from revvy.utils.logger import LogLevel, get_logger
from revvy.utils.stopwatch import Stopwatch
from revvy.utils.subscription import DisposableArray
from revvy.utils.error_reporter import RobotErrorType, revvy_error_handler


class RevvyStatusCode(enum.IntEnum):
    """Exit codes we used to tell the loader what happened"""

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
    """High level class to manage robot state and configuration"""

    def __init__(self):
        self._log = get_logger("RobotManager")
        self.needs_interrupting = True

        self._configuring = False
        self._robot = Robot()

        rc = RemoteController()
        rcs = RemoteControllerScheduler(rc)
        rcs.on_controller_detected(self._on_controller_detected)
        rcs.on_controller_lost(self._on_controller_lost)
        self._remote_controller_scheduler = rcs

        self._sensor_data_subscriptions = DisposableArray()

        self._remote_controller = rc
        self._remote_controller_thread = create_remote_controller_thread(rcs)

        self._robot_state = RobotState(self._robot, self._remote_controller)

        self._scripts = ScriptManager(self._robot)
        self._bg_controlled_scripts = ScriptManager(self._robot)
        self._autonomous = 0
        self._config = empty_robot_config

        self._status_code = RevvyStatusCode.OK
        self.exited = Event()

        self._session_id = 0

        self.on_joystick_action = self._remote_controller.on_joystick_action

        self._robot_state.on(RobotEvent.FATAL_ERROR, lambda *args: self.exit(RevvyStatusCode.ERROR))

        # Start reading status from the robot.
        self._robot_state.start_polling_mcu()

        self.on = self._robot_state.on
        self.trigger = self._robot_state.trigger

        self.on(RobotEvent.MCU_TICK, lambda *args: self.process_autonomous_requests())

        # When anything gets caught by the error handler, send a robot event,
        # so all the connected interfaces get it!
        revvy_error_handler.register_on_error_callback(
            lambda error: self.trigger(RobotEvent.ERROR, error)
        )

    def handle_periodic_control_message(self, message: RemoteControllerCommand):
        self._remote_controller_scheduler.periodic_control_message_handler(message)

    # TODO: not used.
    def validate_config_async(self, motors, sensors, motor_load_power, threshold, callback):
        # TODO: no longer run in background.
        # self.run_in_background(partial(self.validate_config, motors,
        #    sensors, motor_load_power, threshold, callback), '__on_validate_config_requested')

        self._log(
            "Validation request: motors={}, sensors={},pwr:{},sen:{}".format(
                motors, sensors, motor_load_power, threshold
            )
        )

    # TODO: not used.
    def validate_config(self, motors, sensors, motor_load_power, threshold, callback):
        self._log(
            "validate req: motors={}, sensors={},pwr:{},sen:{}".format(
                motors, sensors, motor_load_power, threshold
            )
        )

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
                    motor_port_num, motor_load_power, threshold
                )

            status_string = "unchecked"
            if motor_is_present:
                status_string = "attached"
            elif should_check_port:
                status_string = "detached"

            self._log('Motor port "M{} check result:{}'.format(motor_port_num, status_string))

            motors_result.append(motor_is_present)

        sensors_result = []
        for sensor_idx, sensor_expected_type in enumerate(sensors):
            tested_type = self._robot.__validate_one_sensor_port(sensor_idx, sensor_expected_type)
            sensors_result.append(tested_type)

        callback(success, motors_result, sensors_result)

    # Not sure if this is the right place for this. Maybe an autonomous handler should
    # be linked with the robot's state handler.
    def process_autonomous_requests(self):
        if self._autonomous == "ready":
            req = self.remote_controller.take_autonomous_requests()
            if req == AutonomousModeRequest.START:
                self._bg_controlled_scripts.start_all_scripts()
            elif req == AutonomousModeRequest.PAUSE:
                self._bg_controlled_scripts.pause_all_scripts()
            elif req == AutonomousModeRequest.STOP:
                self._bg_controlled_scripts.stop_all_scripts()
            elif req == AutonomousModeRequest.RESUME:
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
        self._log(f"exit requested with code {status_code}")
        self._status_code = status_code
        if self.needs_interrupting:
            os.kill(os.getpid(), signal.SIGINT)
        self.exited.set()

    def wait_for_exit(self):
        self.exited.wait()
        return self._status_code

    def robot_start(self):
        if self._robot.status.robot_status == RobotStatus.StartingUp:
            self._log("Waiting for MCU")

            try:
                self._ping_robot()
            except TimeoutError:
                pass  # FIXME somehow handle a dead MCU
                # I would add info on the main terminal screen.

        self._log("Connection to MCU established")
        self._robot.status.robot_status = RobotStatus.NotConfigured
        self._robot.play_tune("s_bootup")

    def on_connected(self, device_name):
        """When interface connects"""
        self._log(f"{device_name} device connected!")
        self._robot.status.controller_status = RemoteControllerStatus.ConnectedNoControl
        self._robot.play_tune("s_connect")

    def on_disconnected(self):
        """Reset, play tune"""
        self._log("Device disconnected!")
        self._robot.status.controller_status = RemoteControllerStatus.NotConnected
        self._robot.play_tune("s_disconnect")
        self.reset_configuration()

    def on_connection_changed(self, is_connected):
        self._log("Phone connected" if is_connected else "Phone disconnected")

    def _on_controller_detected(self):
        self._log("Remote controller detected")
        self._robot.status.controller_status = RemoteControllerStatus.Controlled

    def _on_controller_lost(self):
        self._log("Remote controller lost")
        self.trigger(RobotEvent.CONTROLLER_LOST)
        if self._robot.status.controller_status != RemoteControllerStatus.NotConnected:
            self._robot.status.controller_status = RemoteControllerStatus.ConnectedNoControl
            self.reset_configuration()

    def reset_configuration(self):
        """When RC disconnects"""
        self._log("RESET config")
        self._robot.status.robot_status = RobotStatus.NotConfigured
        self._log("RC stopped")
        self._scripts.stop_all_scripts()
        for scr in [self._scripts, self._bg_controlled_scripts]:
            scr.reset()
            scr.assign("Motor", MotorConstants)
            scr.assign("RingLed", RingLed)

        self._remote_controller_thread.stop()
        self._remote_controller.reset()

        for res in self._robot._resources.values():
            res.reset()

        # ping robot, because robot may reset after stopping scripts
        self._ping_robot()

        self._robot.reset()

        revvy_error_handler.read_mcu_errors(self._robot.robot_control)

    def robot_configure(self, config):
        """
        Does the bindings of ports, variables, sensors and motors
        background scripts and button scripts, starts the Remote.
        """

        log = get_logger("ApplyNewConfiguration")
        self._config = config

        self.reset_configuration()

        self._session_id += 1
        self.trigger(RobotEvent.SESSION_ID_CHANGE, self._session_id)
        log(f"New Configuration with session ID: {self._session_id}")

        self._robot.script_variables.reset()

        # Initialize variable slots from config
        scriptvars = []
        for varconf in config.controller.variable_slots:
            slot_idx = varconf["slot"]
            v = self._robot.script_variables.get_variable(slot_idx)
            v.init(varconf["script"], varconf["variable"], 0.0)
            scriptvars.append(v)

        self._bg_controlled_scripts.assign("list_slots", scriptvars)

        # set up motors
        for motor in self._robot.motors:
            motor.configure(config.motors[motor.id])

            # We used to send up power and speed too, but we do not seem to use it anywhere.
            # Angle could however be sent back up.
            # Note that we reduce the ID here, so we do not need that anywhere else.
            # This way we have motors 0-5 in RobotState already. Just a simple array.
            motor.driver.on_status_changed.add(
                lambda p: self._robot_state.set_motor_angle(p.id - 1, p.driver.pos)
            )

        for motor_id in config.drivetrain["left"]:
            self._robot.drivetrain.add_left_motor(self._robot.motors[motor_id])

        for motor_id in config.drivetrain["right"]:
            self._robot.drivetrain.add_right_motor(self._robot.motors[motor_id])

        # Dispose sensor reading subscriptions.
        self._sensor_data_subscriptions.dispose()

        # Re-configure sensors, subscribe to their data's changes.
        for sensor_port in self._robot.sensors:
            log(f"Configuring sensor {sensor_port.id} {config.sensors[sensor_port.id]}")
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

            # Empty sensors do not need a data wrapper subscription.
            if sensor_config:
                # Create a data wrapper that exposes sensor data to the mobile app.
                sensor_data_wrapper_subscription = create_sensor_data_wrapper(
                    sensor_port,
                    sensor_config,
                    lambda event_data: self.trigger(RobotEvent.SENSOR_VALUE_CHANGE, event_data),
                )

                if sensor_data_wrapper_subscription is not None:
                    self._sensor_data_subscriptions.add(sensor_data_wrapper_subscription)

            # Also, I'd love to see all the robot status changes WITHIN the robot in one place,
            # most probably in the robot object.
            # sensor_port.on_status_changed.add(lambda p:
            #  self.trigger(RobotEvent.SENSOR_VALUE_CHANGE, SensorEventData(p.id, p.raw_value)))

        def start_analog_script(src, channels):
            src.start(channels=channels)

        # set up remote controller
        for analog in config.controller.analog:
            script_handle = self._scripts.add_script(analog["script"], config)
            script_handle.on(ScriptEvent.ERROR, self._on_analog_script_error)
            self._remote_controller.on_analog_values(
                analog["channels"], partial(start_analog_script, script_handle)
            )

        # Set up all the bound buttons to run the stored scripts.
        for button, script in enumerate(config.controller.buttons):
            if script:
                log(
                    f"Binding button {button} to script {script.name} with source: \n\n{script.source}\n\n",
                    LogLevel.DEBUG,
                )
                script_handle = self._scripts.add_script(script, config)
                script_handle.assign("list_slots", scriptvars)
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
            bg_script_handle.on(ScriptEvent.ERROR, self._on_bg_script_error)

        self.remote_controller.reset_background_control_state()
        if config.background_initial_state == "running":
            self._bg_controlled_scripts.start_all_scripts()

        self._robot.status.robot_status = RobotStatus.Configured

        # Starts the listening for the messages.
        self._remote_controller_thread.start()

        # When configuration is done, in order to signal the app to enable
        # the play button in autonomous mode, we need to indicate it
        # with sending a status update.
        self.trigger(
            RobotEvent.BACKGROUND_CONTROL_STATE_CHANGE,
            self._remote_controller.background_control_state,
        )

    def _on_script_running(self, script_handle: ScriptHandle, data=None):
        """When script started, notify phone app."""
        self.trigger(
            RobotEvent.PROGRAM_STATUS_CHANGE,
            ProgramStatusChange(script_handle.descriptor.ref_id, ScriptEvent.START),
        )

    def _show_script_error(self, script_handle: ScriptHandle, exception: Exception):
        """
        Blocks thread for 2 seconds!
        On code execution error, do send visible signals
        to the user about the code being broken.
        """
        self._log(f"ERROR in userscript: {script_handle.descriptor.name}", LogLevel.ERROR)
        self._log(f"ERROR:  {str(exception)}", LogLevel.ERROR)
        self._log(
            f"Source that caused the error: \n\n{script_handle.descriptor.source}\n\n",
            LogLevel.ERROR,
        )
        self._log(f"{traceback.format_exc()}", LogLevel.ERROR)

        # Brain bug LED effect with "uh oh" sound.
        self._robot.led.start_animation(RingLed.Bug)
        self._robot.sound.play_tune("s_bug")
        time.sleep(2)
        self._robot.led.start_animation(RingLed.Off)

    def _on_analog_script_error(self, *args):
        """Analog script errors run in separate thread, report them as System errors."""
        revvy_error_handler.report_error(RobotErrorType.SYSTEM, traceback.format_exc())

    def _on_bg_script_error(self, script_handle: ScriptHandle, exception: Exception):

        revvy_error_handler.report_error(
            RobotErrorType.BLOCKLY_BACKGROUND,
            traceback.format_exc(),
            script_handle.descriptor.ref_id,
        )

        # Do it at the and as it's blocking.
        self._show_script_error(script_handle, exception)

    def _on_script_error(self, script_handle: ScriptHandle, exception: Exception):
        """
        Handle runner script errors gracefully, and type out what caused it to bail!
        These are user scripts, so we should consider sending them back via Bluetooth
        """
        self.trigger(
            RobotEvent.PROGRAM_STATUS_CHANGE,
            ProgramStatusChange(script_handle.descriptor.ref_id, ScriptEvent.ERROR),
        )

        revvy_error_handler.report_error(
            RobotErrorType.BLOCKLY_BUTTON, traceback.format_exc(), script_handle.descriptor.ref_id
        )

        # Do it at the and as it's blocking.
        self._show_script_error(script_handle, exception)

    def _on_script_stopped(self, script_handle: ScriptHandle, data=None):
        """If we want to send back script status stopped change, this is the place."""
        # self._log(f'script: {script.name}')
        self.trigger(
            RobotEvent.PROGRAM_STATUS_CHANGE,
            ProgramStatusChange(script_handle.descriptor.ref_id, ScriptEvent.STOP),
        )

    def robot_stop(self):
        """On exiting let's reset all states."""
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
        self._log("pinging")
        while retry_ping:
            retry_ping = False
            try:
                self._robot.ping()
            except (BrokenPipeError, IOError, OSError):
                retry_ping = True
                time.sleep(0.1)
                if timeout != 0 and stopwatch.elapsed > timeout:
                    raise TimeoutError

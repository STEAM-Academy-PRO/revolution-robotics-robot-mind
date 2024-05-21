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
from threading import Event
from typing import Optional

from revvy.mcu.rrrc_control import RevvyTransportBase
from revvy.robot.ports.common import PortInstance
from revvy.robot.ports.sensors.simple import BumperSwitch, ColorSensor, Hcsr04
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
from revvy.robot.robot_state import RobotStatePoller
from revvy.robot.filters.sensor_data import (
    ButtonSensorDataFilter,
    ColorSensorDataFilter,
    SensorDataFilter,
    UltrasonicSensorDataFilter,
)
from revvy.robot.status import RobotStatus, RemoteControllerStatus
from revvy.robot_config import RobotConfig, empty_robot_config
from revvy.scripting.robot_interface import MotorConstants
from revvy.scripting.runtime import ScriptEvent, ScriptHandle, ScriptManager
from revvy.utils.logger import LogLevel, get_logger
from revvy.utils.stopwatch import Stopwatch
from revvy.utils.error_reporter import RobotErrorType, revvy_error_handler
from revvy.bluetooth.data_types import (
    BumperSensorData,
    ColorSensorData,
    UltrasonicSensorData,
)


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

    def __init__(self, interface: RevvyTransportBase) -> None:
        self._log = get_logger("RobotManager")
        self.needs_interrupting = True

        self._configuring = False
        self._robot = Robot(interface)

        rc = RemoteController()
        rcs = RemoteControllerScheduler(rc)
        rcs.on_controller_detected(self._on_controller_detected)
        rcs.on_controller_lost(self._on_controller_lost)
        self._remote_controller_scheduler = rcs

        self.remote_controller = rc
        self._remote_controller_thread = create_remote_controller_thread(rcs)

        self._robot_state = RobotStatePoller(self._robot, self.remote_controller)

        self._scripts = ScriptManager(self._robot)
        self._bg_controlled_scripts = ScriptManager(self._robot)
        self._autonomous = 0
        self._config = empty_robot_config

        self._status_code = RevvyStatusCode.OK
        self.exited = Event()

        self._session_id = 0

        self._robot_state.on(RobotEvent.FATAL_ERROR, lambda *args: self.exit(RevvyStatusCode.ERROR))

        self.on = self._robot_state.on
        self.on_all = self._robot_state.on_all
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
    def validate_config(self, motors, sensors, motor_load_power, threshold, callback) -> None:
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

    # TODO: merge this into RemoteController. All other script kinds are handled there.
    def process_autonomous_requests(self) -> None:
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
    def config(self) -> RobotConfig:
        return self._config

    @property
    def status_code(self) -> RevvyStatusCode:
        return self._status_code

    @property
    def robot(self) -> Robot:
        return self._robot

    def exit(self, status_code: RevvyStatusCode):
        self._log(f"exit requested with code {status_code}")
        if self._status_code == RevvyStatusCode.OK:
            self._status_code = status_code
        if self.needs_interrupting:
            os.kill(os.getpid(), signal.SIGINT)
        self.exited.set()

    def wait_for_exit(self) -> RevvyStatusCode:
        self.exited.wait()
        # make sure we don't get stuck with the speakers on
        self.robot.sound.wait()
        return self._status_code

    def robot_start(self) -> None:
        # Start reading status from the robot.
        self._robot_state.start_polling_mcu()

        if self._robot.status.robot_status == RobotStatus.StartingUp:
            self._log("Waiting for MCU")

            try:
                self._ping_robot()
            except TimeoutError:
                pass  # FIXME somehow handle a dead MCU
                # I would add info on the main terminal screen.

        self._log("Connection to MCU established")
        self._robot.status.update_robot_status(RobotStatus.NotConfigured)

    def on_connected(self, device_name) -> None:
        """When interface connects"""
        self._log(f"{device_name} device connected!")
        self._robot.status.update_controller_status(RemoteControllerStatus.ConnectedNoControl)
        self._robot.play_tune("s_connect")

    def on_disconnected(self) -> None:
        """Reset, play tune"""
        self._log("Device disconnected!")
        self._robot.status.update_controller_status(RemoteControllerStatus.NotConnected)
        self._robot.play_tune("s_disconnect")
        self.reset_configuration()

    def on_connection_changed(self, is_connected) -> None:
        self._log("Phone connected" if is_connected else "Phone disconnected")

    def _on_controller_detected(self) -> None:
        self._log("Remote controller detected")
        self._robot.status.update_controller_status(RemoteControllerStatus.Controlled)

    def _on_controller_lost(self) -> None:
        self._log("Remote controller lost")
        self.trigger(RobotEvent.CONTROLLER_LOST)
        if self._robot.status.controller_status != RemoteControllerStatus.NotConnected:
            self._robot.status.update_controller_status(RemoteControllerStatus.ConnectedNoControl)
            self.reset_configuration()

    def reset_configuration(self) -> None:
        """When RC disconnects"""
        self._log("Reset robot config")
        self._robot.status.update_robot_status(RobotStatus.NotConfigured)
        self._scripts.stop_all_scripts()
        for scr in [self._scripts, self._bg_controlled_scripts]:
            scr.reset()
            scr.assign("Motor", MotorConstants)
            scr.assign("RingLed", RingLed)

        self._remote_controller_thread.stop()
        self.remote_controller.reset()

        for res in self._robot._resources.values():
            res.reset()

        # ping robot, because robot may reset after stopping scripts
        self._ping_robot()

        self._robot.reset()

        revvy_error_handler.read_mcu_errors(self._robot.robot_control)

    def robot_configure(self, config: RobotConfig):
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

        # Initialize variable slots from config
        scriptvars = []
        for varconf in config.controller.variable_slots:
            v = self._robot.script_variables.slot(varconf["slot"])
            v.bind(varconf["script"], varconf["variable"])
            scriptvars.append(v)

        self._bg_controlled_scripts.assign("list_slots", scriptvars)

        # set up motors
        for motor_port in self._robot.motors:
            motor_config = config.motors[motor_port.id]
            log(f"Configuring motor {motor_port.id} {motor_config}", LogLevel.DEBUG)
            motor_port.configure(motor_config)

        for motor_id in config.drivetrain.left:
            self._robot.drivetrain.add_left_motor(self._robot.motors[motor_id])

        for motor_id in config.drivetrain.right:
            self._robot.drivetrain.add_right_motor(self._robot.motors[motor_id])

        # configure sensors, attach filters to their data change.
        for sensor_port in self._robot.sensors:
            sensor_config = config.sensors[sensor_port.id]
            log(f"Configuring sensor {sensor_port.id} {sensor_config}", LogLevel.DEBUG)

            sensor_port.configure(sensor_config)

            # Create a data wrapper that exposes sensor data to the mobile app.
            filter = self._create_sensor_data_filter(sensor_port)

            if filter:
                # Pipe the data changes into the filter.
                sensor_port.driver.on_status_changed.add(filter.update)

        # set up remote controller
        for analog in config.controller.analog:
            script_handle = self._scripts.add_script(analog["script"], config)
            script_handle.on(ScriptEvent.ERROR, self._on_analog_script_error)
            self.remote_controller.on_analog_values(analog["channels"], script_handle)

        # Set up all the bound buttons to run the stored scripts.
        for button, script in enumerate(config.controller.buttons):
            if script:
                log(
                    f"Binding button {button} to script {script.name} with source: \n\n{script.source}\n\n",
                    LogLevel.DEBUG,
                )
                script_handle = self._scripts.add_script(script, config)
                script_handle.assign("list_slots", scriptvars)
                self.remote_controller.link_button_to_runner(button, script_handle)

                script_handle.on(ScriptEvent.START, self._on_button_script_running)
                script_handle.on(ScriptEvent.STOP, self._on_button_script_stopped)
                script_handle.on(ScriptEvent.ERROR, self._on_button_script_error)

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

        self._robot.status.update_robot_status(RobotStatus.Configured)

        # Starts the listening for the messages.
        self._remote_controller_thread.start()

        # When configuration is done, in order to signal the app to enable
        # the play button in autonomous mode, we need to indicate it
        # with sending a status update.
        self.trigger(
            RobotEvent.BACKGROUND_CONTROL_STATE_CHANGE,
            self.remote_controller.background_control_state,
        )

    def _create_sensor_data_filter(
        self,
        sensor_port: PortInstance,
    ) -> Optional[SensorDataFilter]:
        """
        Create wrappers that smooth and throttle sensor reading
        so their output is more suitable for BLE.
        """

        # Currently our sensors send data with too-high sampling rates so these
        # serve as an extra data layer over the sensor port readings to debounce/throttle
        # the surfacing values.
        #
        # Ideally, we'll dig down into the bottoms of the drivers and clean the
        # data there and only surface it when it's actually good and reliable.
        # Until now, here is a wrapper.

        if isinstance(sensor_port.driver, Hcsr04):
            self._log(f"ultrasonic on port {sensor_port.id}")
            return UltrasonicSensorDataFilter(
                lambda value: self.trigger(
                    RobotEvent.SENSOR_VALUE_CHANGE,
                    UltrasonicSensorData(sensor_port.id, value),
                )
            )

        elif isinstance(sensor_port.driver, BumperSwitch):
            self._log(f"button {sensor_port.id}")
            return ButtonSensorDataFilter(
                lambda value: self.trigger(
                    RobotEvent.SENSOR_VALUE_CHANGE,
                    BumperSensorData(sensor_port.id, value),
                )
            )

        elif isinstance(sensor_port.driver, ColorSensor):
            self._log(f"color sensor {sensor_port.id}")
            return ColorSensorDataFilter(
                lambda value: self.trigger(
                    RobotEvent.SENSOR_VALUE_CHANGE,
                    ColorSensorData(sensor_port.id, value),
                )
            )

    def _show_script_error(self, script_handle: ScriptHandle, exception: Exception):
        """
        Blocks thread for 2 seconds!
        On code execution error, do send visible signals
        to the user about the code being broken.
        """
        self._log(f"ERROR in user script: {script_handle.descriptor.name}", LogLevel.ERROR)
        self._log(f"ERROR: {str(exception)}", LogLevel.ERROR)
        self._log(
            f"Source that caused the error: \n\n{script_handle.descriptor.source}\n", LogLevel.ERROR
        )
        self._log(f"{traceback.format_exc()}", LogLevel.ERROR)

        # Brain bug LED effect with "uh oh" sound.
        self._robot.led.start_animation(RingLed.Bug)
        self._robot.sound.play_tune_blocking("s_bug")
        self._robot.led.start_animation(RingLed.Off)

    def _on_analog_script_error(self, script_handle: ScriptHandle, exception: Exception):
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

    def _report_button_script_state_change(self, script_handle: ScriptHandle, state: ScriptEvent):
        assert script_handle.descriptor.ref_id is not None
        self.trigger(
            RobotEvent.PROGRAM_STATUS_CHANGE,
            ProgramStatusChange(script_handle.descriptor.ref_id, state),
        )

    def _on_button_script_running(self, script_handle: ScriptHandle, data):
        """When script started, notify phone app."""
        self._report_button_script_state_change(script_handle, ScriptEvent.START)

    def _on_button_script_error(self, script_handle: ScriptHandle, exception: Exception):
        """
        Handle runner script errors gracefully, and type out what caused it to bail!
        These are user scripts, so we should consider sending them back via Bluetooth
        """
        self._report_button_script_state_change(script_handle, ScriptEvent.ERROR)

        revvy_error_handler.report_error(
            RobotErrorType.BLOCKLY_BUTTON, traceback.format_exc(), script_handle.descriptor.ref_id
        )

        # Do it at the end as it's blocking.
        self._show_script_error(script_handle, exception)

    def _on_button_script_stopped(self, script_handle: ScriptHandle, data):
        self._report_button_script_state_change(script_handle, ScriptEvent.STOP)

    def robot_stop(self) -> None:
        """On exiting let's reset all states."""
        self._robot_state.stop_polling_mcu()
        self._robot.status.update_controller_status(RemoteControllerStatus.NotConnected)
        self._robot.status.update_robot_status(RobotStatus.Stopped)
        self._remote_controller_thread.exit()
        self.trigger(RobotEvent.STOPPED)
        self._scripts.reset()
        self._robot.stop()

    def _ping_robot(self, timeout=0) -> None:
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

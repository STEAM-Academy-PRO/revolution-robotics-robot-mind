""" Handles the short messages from the device. """

import struct
from typing import Callable, Optional

from pybleno import BlenoPrimaryService
from revvy.bluetooth.ble_characteristics import (
    GyroCharacteristic,
    MobileToBrainFunctionCharacteristic,
    ProgramStatusCharacteristic,
    ReadVariableCharacteristic,
    BackgroundProgramControlCharacteristic,
    SensorCharacteristic,
    TimerCharacteristic,
    ValidateConfigCharacteristic,
    ValidateState,
)
from revvy.bluetooth.queue_characteristic import QueueCharacteristic
from revvy.bluetooth.data_types import (
    BackgroundControlState,
    GyroData,
    ScriptVariables,
    SensorData,
    TimerData,
)
from revvy.robot.rc_message_parser import parse_control_message
from revvy.robot.robot_events import ProgramStatusChange
from revvy.robot_manager import RobotManager
from revvy.scripting.runtime import ScriptEvent

from revvy.utils.error_reporter import RobotError
from revvy.utils.logger import get_logger

from revvy.robot.remote_controller import BleAutonomousCmd, RemoteControllerCommand

NUM_MOTOR_PORTS = 6
NUM_SENSOR_PORTS = 4

log = get_logger("Live Message Service")


class LiveMessageService(BlenoPrimaryService):
    """Handles short messages on the Bluetooth interface"""

    def __init__(self, robot_manager: RobotManager):
        self._message_handler = None

        self._robot_manager = robot_manager

        self._read_variable_characteristic = ReadVariableCharacteristic(
            "d4ad2a7b-57be-4803-8df0-6807073961ad", b"Variable Slots"
        )
        self._gyro_characteristic = GyroCharacteristic(
            "d5bd4300-7c49-4108-8500-8716ffd39de8", b"Gyro"
        )
        self._orientation_characteristic = GyroCharacteristic(
            "4337a7c2-cae9-4c88-8908-8810ee013fcb", b"Orientation"
        )
        self._timer_characteristic = TimerCharacteristic(
            "c0e913da-5fdd-4a17-90b4-47758d449306", b"Timer"
        )
        self._program_status_characteristic = ProgramStatusCharacteristic(
            "7b988246-56c3-4a90-a6e8-e823ea287730", b"ProgramStatus"
        )
        self._background_program_control_characteristic = BackgroundProgramControlCharacteristic(
            "53881a54-d519-40f7-8cbf-d43ced67f315", b"State Control", self.state_control_callback
        )
        self._error_reporting_characteristic = QueueCharacteristic(
            "0a0a8fa3-4c8f-44eb-892f-2bb8a6e163ca", b"Error Reporting"
        )

        self._sensor_characteristics = [
            SensorCharacteristic("135032e6-3e86-404f-b0a9-953fd46dcb17", b"Sensor 1"),
            SensorCharacteristic("36e944ef-34fe-4de2-9310-394d482e20e6", b"Sensor 2"),
            SensorCharacteristic("b3a71566-9af2-4c9d-bc4a-6f754ab6fcf0", b"Sensor 3"),
            SensorCharacteristic("9ace575c-0b70-4ed5-96f1-979a8eadbc6b", b"Sensor 4"),
        ]

        self._mobile_to_brain = MobileToBrainFunctionCharacteristic(
            "7486bec3-bb6b-4abd-a9ca-20adc281a0a4",
            20,
            20,
            b"simpleControl",
            self.control_message_handler,
        )

        self._validate_config_characteristic = ValidateConfigCharacteristic(
            "ad635567-07a7-4c8a-8765-d504dac7c86f",
            b"Validate configuration",
            self.validate_config_callback,
        )

        super().__init__(
            {
                "uuid": "d2d5558c-5b9d-11e9-8647-d663bd873d93",
                "characteristics": [
                    self._mobile_to_brain,
                    self._validate_config_characteristic,
                    *self._sensor_characteristics,
                    self._gyro_characteristic,
                    self._orientation_characteristic,
                    self._read_variable_characteristic,
                    self._background_program_control_characteristic,
                    self._timer_characteristic,
                    self._program_status_characteristic,
                    self._error_reporting_characteristic,
                ],
            }
        )

    def reset(self, *args) -> None:
        """Reset BLE characteristic values to prevent reading back old values in a new session."""
        self._read_variable_characteristic.resetValue()
        self._background_program_control_characteristic.updateValue([])
        self._program_status_characteristic.resetValue()
        for sensor in self._sensor_characteristics:
            sensor.resetValue()

    def validate_config_callback(self, data: bytes) -> bool:
        # FIXME: Currently unused
        motor_bitmask, sensor0, sensor1, sensor2, sensor3, motor_load_power, threshold = (
            struct.unpack("7B", data)
        )

        current_state = self._validate_config_characteristic.state
        if current_state == ValidateState.IN_PROGRESS:
            return False

        motors = [(motor_bitmask >> i) & 1 for i in range(NUM_MOTOR_PORTS)]

        def validation_callback(success, motors, sensors) -> None:
            self.set_validation_result(success, motors, sensors)
            self._validate_config_characteristic.updateValue(
                ValidateState.IN_PROGRESS, motor_bitmask, sensors
            )

        self._robot_manager.validate_config_async(
            motors,
            [sensor0, sensor1, sensor2, sensor3],
            motor_load_power,
            threshold,
            validation_callback,
        )

        return True

    def set_validation_result(self, success: bool, motors: list, sensors: list):
        # FIXME: Currently unused

        valitation_state = ValidateState.UNKNOWN
        if success:
            valitation_state = ValidateState.DONE

        if len(motors) != NUM_MOTOR_PORTS:
            log(f"set_validation_result::invalid motors response: {motors}")

        motor_bitmask = 0
        for i in range(max(NUM_MOTOR_PORTS, len(motors))):
            motor_bit = 0
            if isinstance(motors[i], bool):
                motor_bit = motors[i]
            motor_bitmask |= motor_bit << i

        if len(sensors) != NUM_SENSOR_PORTS:
            sensors = [False] * NUM_SENSOR_PORTS

        self._validate_config_characteristic.updateValue(valitation_state, motor_bitmask, sensors)

    def control_message_handler(self, data: bytearray) -> bool:
        """
        Simple control callback is run each time new controller data
        representing full state of joystick is sent over a BLE characteristic
        Analog values: X and Y axes of a joystick, mapped to 0-255, where 127
        is the middle value representing joystick axis in neutral state.
        """

        command = parse_control_message(data)
        self._robot_manager.handle_periodic_control_message(command)
        return True

    def state_control_callback(self, data: bytes):
        """Autonomous mode play/pause/stop/reset button from mobile to brain"""

        log(f"state_control_callback, coming from the mobile. {data}")
        self._robot_manager.handle_periodic_control_message(
            RemoteControllerCommand(
                analog=bytearray(b"\x7f\x7f\x00\x00\x00\x00\x00\x00\x00\x00"),
                buttons=[False] * 32,
                background_command=BleAutonomousCmd(int.from_bytes(data[2:], byteorder="big")),
                next_deadline=None,
            )
        )

    def update_sensor(self, emitter, sensor_data: SensorData):
        """Send back sensor value to mobile."""
        try:
            self._sensor_characteristics[sensor_data.port_id].updateValue(sensor_data)
        except IndexError as e:
            log(f"Sensor data update failed: {e}")

    def update_program_status(self, emitter, change: ProgramStatusChange):
        """Update the status of a button-triggered script"""

        self._program_status_characteristic.updateButtonStatus(change.id, change.status.value)

    def update_session_id(self, emitter, value: int):
        """Send back session_id to mobile."""
        data = list(struct.pack("<I", value))
        # Maybe this was supposed to be used for detecting MCU reset in the mobile, but
        # currently it's not used.
        self._mobile_to_brain.updateValue(data)

    def update_gyro(self, data: GyroData):
        """Send back gyro sensor value to mobile."""
        # TODO: unused?
        self._gyro_characteristic.updateValue(data)

    def update_orientation(self, emitter, data: GyroData):
        """Send back orientation to mobile. Used to display the yaw of the robot"""
        self._orientation_characteristic.updateValue(data)

    def update_timer(self, emitter, data: TimerData):
        """Send back timer tick to mobile."""
        self._timer_characteristic.updateValue(data)

    def report_error(self, data: RobotError, on_ready: Optional[Callable[[], None]] = None):
        log(f"Sending Error: {data}")
        self._error_reporting_characteristic.sendQueued(data.__bytes__(), on_ready)

    def update_script_variables(self, emitter, script_variables: ScriptVariables):
        """
        In the mobile app, this data shows up when we track variables.
        By characteristic protocol - maximum slots in BLE message is 4.
        """
        self._read_variable_characteristic.updateValue(script_variables)

    def update_state_control(self, emitter, state: BackgroundControlState):
        """Send back the background programs' state."""
        log(f"state control update, {state}")
        self._background_program_control_characteristic.updateValue(state)

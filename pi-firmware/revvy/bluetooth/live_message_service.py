""" Handles the short messages from the device. """

import struct

from pybleno import BlenoPrimaryService
from revvy.bluetooth.ble_characteristics import (
    GyroCharacteristic,
    MobileToBrainFunctionCharacteristic,
    MotorCharacteristic,
    ProgramStatusCharacteristic,
    ReadVariableCharacteristic,
    BackgroundProgramControlCharacteristic,
    SensorCharacteristic,
    TimerCharacteristic,
    ValidateConfigCharacteristic,
)
from revvy.bluetooth.queue_characteristic import QueueCharacteristic
from revvy.bluetooth.data_types import (
    MotorData,
    BackgroundControlState,
    GyroData,
    ScriptVariables,
    SensorData,
    TimerData,
)
from revvy.bluetooth.validate_config_statuses import (
    VALIDATE_CONFIG_STATE_DONE,
    VALIDATE_CONFIG_STATE_IN_PROGRESS,
    VALIDATE_CONFIG_STATE_UNKNOWN,
)
from revvy.robot.rc_message_parser import parse_control_message
from revvy.robot_manager import RobotManager
from revvy.scripting.runtime import ScriptEvent

from revvy.utils.logger import get_logger

from revvy.robot.remote_controller import RemoteControllerCommand

NUM_MOTOR_PORTS = 6
NUM_SENSOR_PORTS = 4

log = get_logger("Live Message Service")


class LiveMessageService(BlenoPrimaryService):
    """Handles short messages on the Bluetooth interface"""

    def __init__(self, robot_manager: RobotManager):
        self._message_handler = None

        self._robot_manager = robot_manager

        # on_joystick_action is a callback that should run when LiveMessageService
        # detects that joystick action is received from mobile app over a curtain
        # characteristic
        # self.__joystick_action_cb = None

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

        self._motor_characteristics = [
            MotorCharacteristic("4bdfb409-93cc-433a-83bd-7f4f8e7eaf54", b"Motor 1"),
            MotorCharacteristic("454885b9-c9d1-4988-9893-a0437d5e6e9f", b"Motor 2"),
            MotorCharacteristic("00fcd93b-0c3c-4940-aac1-b4c21fac3420", b"Motor 3"),
            MotorCharacteristic("49aaeaa4-bb74-4f84-aa8f-acf46e5cf922", b"Motor 4"),
            MotorCharacteristic("ceea8e45-5ff9-4325-be13-48cf40c0e0c3", b"Motor 5"),
            MotorCharacteristic("8e4c474f-188e-4d2a-910a-cf66f674f569", b"Motor 6"),
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
                    *self._motor_characteristics,
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

    def validate_config_callback(self, data):
        # FIXME: Currently unused
        motor_bitmask, sensor0, sensor1, sensor2, sensor3, motor_load_power, threshold = (
            struct.unpack("BBBBBBB", data)
        )

        current_state = self._validate_config_characteristic.get_state()
        if current_state == VALIDATE_CONFIG_STATE_IN_PROGRESS:
            return False

        motors = [(motor_bitmask >> i) & 1 for i in range(NUM_MOTOR_PORTS)]

        def validation_callback(success, motors, sensors):
            self.set_validation_result(success, motors, sensors)
            self._validate_config_characteristic.update_validate_config_result(
                VALIDATE_CONFIG_STATE_IN_PROGRESS, motor_bitmask, sensors
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

        valitation_state = VALIDATE_CONFIG_STATE_UNKNOWN
        if success:
            valitation_state = VALIDATE_CONFIG_STATE_DONE

        if len(motors) != NUM_MOTOR_PORTS:
            log("set_validation_result::invalid motors response: ", motors)

        motor_bitmask = 0
        for i in range(max(NUM_MOTOR_PORTS, len(motors))):
            motor_bit = 0
            if isinstance(motors[i], bool):
                motor_bit = motors[i]
            motor_bitmask |= motor_bit << i

        if len(sensors) == NUM_SENSOR_PORTS:
            s0, s1, s2, s3 = sensors
        else:
            s0 = s1 = s2 = s3 = False

        self._validate_config_characteristic.update_validate_config_result(
            valitation_state, motor_bitmask, [s0, s1, s2, s3]
        )

    def control_message_handler(self, data: bytearray):
        """
        Simple control callback is run each time new controller data
        representing full state of joystick is sent over a BLE characteristic
        Analog values: X and Y axes of a joystick, mapped to 0-255, where 127
        is the middle value representing joystick axis in neutral state.
        """

        def joystick_axis_is_neutral(value):
            """
            Value is in 1 byte range 0-255, with 127 being the middle position
            of a joystick along that axis
            """
            return value == 127

        def joystick_xy_is_moved(analog_values):
            if len(analog_values) < 2:
                return False

            x_value = analog_values[0]
            y_value = analog_values[1]
            for v in [x_value, y_value]:
                if not joystick_axis_is_neutral(v):
                    return True
            return False

        command = parse_control_message(data)

        # This seems like it's doing nothing...
        joystick_xy_action = joystick_xy_is_moved(command.analog)
        joystick_button_action = any(command.buttons)

        # log(f'data: {str(data)}')
        # log(f'analog_values: {str(analog_values)}')
        # log(f'deadline_packed: {str(deadline_packed)}')
        # log(f'button_values: {str(button_values)}')

        # First user input action triggers global timer
        if joystick_xy_action or joystick_button_action:
            # log(f'joystick_xy_action: {str(joystick_xy_action)}')
            self._robot_manager.on_joystick_action()

        self._robot_manager.handle_periodic_control_message(command)
        return True

    def state_control_callback(self, data):
        """Autonomous mode play/pause/stop/reset button from mobile to brain"""

        log(f"state_control_callback, coming from the mobile. {data}")
        self._robot_manager.handle_periodic_control_message(
            RemoteControllerCommand(
                analog=bytearray(b"\x7f\x7f\x00\x00\x00\x00\x00\x00\x00\x00"),
                buttons=[False] * 32,
                background_command=int.from_bytes(data[2:], byteorder="big"),
                next_deadline=None,
            )
        )

    def update_sensor(self, sensor_data: SensorData):
        """Send back sensor value to mobile."""
        if 0 < sensor_data.port_id <= len(self._sensor_characteristics):
            self._sensor_characteristics[sensor_data.port_id - 1].update(sensor_data)

    def update_program_status(self, button_id: int, status: ScriptEvent):
        """Update the status of a button-triggered script"""

        self._program_status_characteristic.update_button_value(button_id, status.value)

    def update_motor(self, motor, data: MotorData):
        """Send back motor angle value to mobile."""
        # TODO: unused?
        if 0 <= motor < len(self._motor_characteristics):
            self._motor_characteristics[motor].update(data)

    def update_session_id(self, value):
        """Send back session_id to mobile."""
        data = list(struct.pack("<I", value))
        # Maybe this was supposed to be used for detecting MCU reset in the mobile, but
        # currently it's not used.
        self._mobile_to_brain.update(data)

    def update_gyro(self, data: GyroData):
        """Send back gyro sensor value to mobile."""
        # TODO: unused?
        self._gyro_characteristic.update(data)

    def update_orientation(self, data: GyroData):
        """Send back orientation to mobile. Used to display the yaw of the robot"""
        self._orientation_characteristic.update(data)

    def update_timer(self, data: TimerData):
        """Send back timer tick to mobile."""
        self._timer_characteristic.update(data)

    def report_error(self, data):
        log(f"Sending Error: {data}")
        self._error_reporting_characteristic.update(data)

    def update_script_variables(self, script_variables: ScriptVariables):
        """
        In the mobile app, this data shows up when we track variables.
        By characteristic protocol - maximum slots in BLE message is 4.
        """
        self._read_variable_characteristic.update(script_variables)

    def update_state_control(self, state: BackgroundControlState):
        """Send back the background programs' state."""
        log(f"state control update, {state}")
        self._background_program_control_characteristic.update(state)

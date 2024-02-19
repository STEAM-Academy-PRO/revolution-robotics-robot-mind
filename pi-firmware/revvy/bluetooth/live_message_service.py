""" Handles the short messages from the device. """

import struct

from pybleno import BlenoPrimaryService
from revvy.bluetooth.ble_characteristics import GyroCharacteristic, MobileToBrainFunctionCharacteristic, MotorCharacteristic, ProgramStatusCharacteristic, ReadVariableCharacteristic, BackgroundProgramControlCharacteristic, SensorCharacteristic, TimerCharacteristic, ValidateConfigCharacteristic
from revvy.bluetooth.queue_characteristic import QueueCharacteristic
from revvy.bluetooth.validate_config_statuses import VALIDATE_CONFIG_STATE_DONE, VALIDATE_CONFIG_STATE_IN_PROGRESS, VALIDATE_CONFIG_STATE_UNKNOWN
from revvy.robot.rc_message_parser import parse_control_message
from revvy.robot_manager import RobotManager

from revvy.utils.logger import get_logger

from revvy.robot.remote_controller import RemoteControllerCommand

NUM_MOTOR_PORTS = 6
NUM_SENSOR_PORTS = 4

log = get_logger("Live Message Service", off=False)

class LiveMessageService(BlenoPrimaryService):
    """ Handles short messages on the Bluetooth interface"""
    def __init__(self, robot_manager: RobotManager):
        self._message_handler = None

        self._robot_manager = robot_manager

        # on_joystick_action is a callback that should run when LiveMessageService
        # detects that joystick action is received from mobile app over a curtain
        # characteristic
        # self.__joystick_action_cb = None

        self._read_variable_characteristic = ReadVariableCharacteristic('d4ad2a7b-57be-4803-8df0-6807073961ad', b'Variable Slots')
        self._gyro_characteristic = GyroCharacteristic('d5bd4300-7c49-4108-8500-8716ffd39de8', b'Gyro')
        self._orientation_characteristic = GyroCharacteristic('4337a7c2-cae9-4c88-8908-8810ee013fcb', b'Orientation')
        self._timer_characteristic = TimerCharacteristic('c0e913da-5fdd-4a17-90b4-47758d449306', b'Timer')
        self._program_status_characteristic = ProgramStatusCharacteristic('7b988246-56c3-4a90-a6e8-e823ea287730', b'ProgramStatus')
        self._background_program_control_characteristic = BackgroundProgramControlCharacteristic(
            '53881a54-d519-40f7-8cbf-d43ced67f315', b'State Control', self.state_control_callback
        )
        self._error_reporting_characteristic = QueueCharacteristic('0a0a8fa3-4c8f-44eb-892f-2bb8a6e163ca', b'Error Reporting')

        self._sensor_characteristics = [
            SensorCharacteristic('135032e6-3e86-404f-b0a9-953fd46dcb17', b'Sensor 1'),
            SensorCharacteristic('36e944ef-34fe-4de2-9310-394d482e20e6', b'Sensor 2'),
            SensorCharacteristic('b3a71566-9af2-4c9d-bc4a-6f754ab6fcf0', b'Sensor 3'),
            SensorCharacteristic('9ace575c-0b70-4ed5-96f1-979a8eadbc6b', b'Sensor 4'),
        ]

        self._motor_characteristics = [
            MotorCharacteristic('4bdfb409-93cc-433a-83bd-7f4f8e7eaf54', b'Motor 1'),
            MotorCharacteristic('454885b9-c9d1-4988-9893-a0437d5e6e9f', b'Motor 2'),
            MotorCharacteristic('00fcd93b-0c3c-4940-aac1-b4c21fac3420', b'Motor 3'),
            MotorCharacteristic('49aaeaa4-bb74-4f84-aa8f-acf46e5cf922', b'Motor 4'),
            MotorCharacteristic('ceea8e45-5ff9-4325-be13-48cf40c0e0c3', b'Motor 5'),
            MotorCharacteristic('8e4c474f-188e-4d2a-910a-cf66f674f569', b'Motor 6'),
        ]

        self._mobile_to_brain = MobileToBrainFunctionCharacteristic(
            '7486bec3-bb6b-4abd-a9ca-20adc281a0a4', 20, 20, b'simpleControl',
             self.control_message_handler)

        self._validate_config_characteristic = ValidateConfigCharacteristic(
            'ad635567-07a7-4c8a-8765-d504dac7c86f', b'Validate configuration',
             self.validate_config_callback)

        self._buf_gyro = b'\xff'
        self._buf_orientation = b'\xff'
        self._buf_script_variables = b'\xff'

        super().__init__({
            'uuid':            'd2d5558c-5b9d-11e9-8647-d663bd873d93',
            'characteristics': [
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
                self._error_reporting_characteristic
            ]
        })

    def validate_config_callback(self, data):
        # FIXME: Currently unused
        motor_bitmask, sensor0, sensor1, sensor2, sensor3, \
        motor_load_power, threshold = \
            struct.unpack('BBBBBBB', data)

        current_state = self._validate_config_characteristic.get_state()
        if current_state == VALIDATE_CONFIG_STATE_IN_PROGRESS:
            return False

        motors = [(motor_bitmask >> i) & 1 for i in range(NUM_MOTOR_PORTS)]

        def validation_callback(success, motors, sensors):
            self.set_validation_result(success, motors, sensors)
            self._validate_config_characteristic.update_validate_config_result(
                VALIDATE_CONFIG_STATE_IN_PROGRESS,
                motor_bitmask,
                sensors)

        self._robot_manager.validate_config_async(
            motors, [sensor0, sensor1, sensor2, sensor3],
            motor_load_power,
            threshold,
            validation_callback
            )

        return True

    def set_validation_result(self, success: bool,
        motors: list, sensors: list):
        # FIXME: Currently unused

        valitation_state = VALIDATE_CONFIG_STATE_UNKNOWN
        if success:
            valitation_state = VALIDATE_CONFIG_STATE_DONE

        if len(motors) != NUM_MOTOR_PORTS:
            log('set_validation_result::invalid motors response: ', motors)

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
          valitation_state,
          motor_bitmask,
          [s0, s1, s2, s3])


    def control_message_handler(self, data):
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

        message_handler = self._robot_manager.handle_periodic_control_message
        if message_handler:
            message_handler(command)
        return True


    def state_control_callback(self, data):
        """ Autonomous mode play/pause/stop/reset button from mobile to brain """

        log(f"state_control_callback, coming from the mobile. {data}")
        message_handler = self._robot_manager.handle_periodic_control_message
        if message_handler:
            message_handler(RemoteControllerCommand(analog=bytearray(b'\x7f\x7f\x00\x00\x00\x00\x00\x00\x00\x00'),
                                                    buttons=[False]*32,
                                                    background_command=int.from_bytes(data[2:], byteorder='big'),
                                                    next_deadline=None))

    def update_sensor(self, sensor, value):
        """ Send back sensor value to mobile. """
        if 0 < sensor <= len(self._sensor_characteristics):
            self._sensor_characteristics[sensor - 1].update(value)

    def update_program_status(self, button_id: int, status: int):
        """
         It might be possible that BLE misses a packet. If that's the case,
         we still want to encode all the program statuses in the message,
         so we keep the struct up-to-date.
        """

        self._program_status_characteristic.update_button_value(button_id, status)

    def update_motor(self, motor, power, speed, position):
        """ Send back motor angle value to mobile. """
        # TODO: unused?
        if 0 <= motor < len(self._motor_characteristics):
            data = list(struct.pack(">flb", speed, position, power))
            self._motor_characteristics[motor].update(data)

    def update_session_id(self, value):
        """ Send back session_id to mobile. """
        data = list(struct.pack('<I', value))
        # Maybe this was supposed to be used for detecting MCU reset in the mobile, but
        # currently it's not used.
        self._mobile_to_brain.update(data)

    def update_gyro(self, vector_list):
        """ Send back gyro sensor value to mobile. """
        # TODO: unused?
        if type(vector_list) is list:
            buf = struct.pack('%sf' % len(vector_list), *vector_list)
            if self._buf_gyro is not buf:
                self._buf_gyro = buf
                self._gyro_characteristic.update(self._buf_gyro)

    def update_orientation(self, vector_list):
        """ Send back orientation to mobile. Used to display the yaw of the robot """
        if type(vector_list) is list:
            buf = struct.pack('%sf' % len(vector_list), *vector_list)
            if self._buf_orientation is not buf:
                self._buf_orientation = buf
                self._orientation_characteristic.update(self._buf_orientation)

    def update_timer(self, data):
        """ Send back timer tick every second to mobile. """
        buf = list(struct.pack(">bf", 4, round(data, 0)))
        self._timer_characteristic.update(buf)


    def report_error(self, data):
        log(f'Sending Error: {data}')
        self._error_reporting_characteristic.update(data)

    def update_script_variables(self, script_variables):
        """
            In the mobile app, this data shows up when we track variables.
            By characteristic protocol - maximum slots in BLE message is 4.
        """

        # I believe this should be a constant that's coming from one centralized place, rather
        # be wired in here. If this script sends more variables, we'll never know.
        MAX_VARIABLE_SLOTS = 4

        # Message format:
        # offset:  0    1  2  3  4    5  6  7  8    9  10 11 12   13 14 15 16
        # values:  0A | BB BB BB BB | CC CC CC CC | DD DD DD DD | EE EE EE EE
        # A - bitmask consists of 4 bits. if bit is set - value has been set
        #     by scripts. If bit is not set - value has never been changed yet,
        #     due to script not run at all, or script has not yet set the value
        #     and ReportVariableChanged has not been called for this slot

        # BB - float value for Slot 1
        # CC - float value for Slot 2
        # DD - float value for Slot 3
        # EE - float value for Slot 4

        # In the end the user of this packet receives info about 4 slots, current
        # value of each slot, has the value in this slot been set at least once

        mask = 0
        valuebuf = b''

        for slot_idx in range(MAX_VARIABLE_SLOTS):
            value = script_variables[slot_idx]
            if (value):
                mask = mask | (1 << slot_idx)
            else:
                value = 0.0
            valuebuf += struct.pack('f', value)

        maskbuf = struct.pack('B', mask)
        msg = maskbuf + valuebuf

        self._read_variable_characteristic.update(msg)

    def update_state_control(self, state):
        """ Send back the background programs' state. """
        log(f"state control update, {state}")
        data = list(struct.pack(">bl", 4, state))
        self._background_program_control_characteristic.update(data)



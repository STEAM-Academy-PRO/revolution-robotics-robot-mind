""" Standardized Robot Events to all """

from typing import NamedTuple

from revvy.scripting.runtime import ScriptEvent


class RobotEvent:
    """
        Robot communication events: these events are sent from the robot towards
        any interface that's subscribed to robot events.
    """
    BATTERY_CHANGE = "battery_change"
    ORIENTATION_CHANGE= "orientation_change"
    MOTOR_CHANGE="motor_change"
    SCRIPT_VARIABLE_CHANGE="script_variable_change"
    PROGRAM_STATUS_CHANGE="program_status_change"
    BACKGROUND_CONTROL_STATE_CHANGE="background_control_state_change"
    SENSOR_VALUE_CHANGE="sensor_value_change"
    TIMER_TICK="timer_tick"
    FATAL_ERROR="fatal_error"
    # Temporarily, for background processes to be triggered.
    MCU_TICK="mcu_tick"
    DISCONNECT="disconnect"
    SESSION_ID_CHANGE="session_id_change"
    STOPPED="stopped"

    CAMERA_STARTED="camera_started"
    CAMERA_STOPPED="camera_stopped"
    CAMERA_ERROR="camera_error"


class ProgramStatusChange(NamedTuple):
    """ Which program ID, what's the status of the program? """
    id: int
    status: ScriptEvent

class MotorChangeData(NamedTuple):
    """ We send back motor status changes, regularly """
    id: int
    power: int
    speed: int
    pos: int

class SensorEventData(NamedTuple):
    """ Ultrasonic sensor and button data. Not pretty, would be better with ints. """
    id: int
    raw_value: any

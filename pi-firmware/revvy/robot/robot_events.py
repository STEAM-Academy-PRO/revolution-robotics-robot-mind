""" Standardized Robot Events to all """

class RobotEvent:
    """
        Robot communication events: these events are sent from the robot towards
        any interface that's subscribed to robot events.
    """
    BATTERY_CHANGE = "battery_change"
    ORIENTATION_CHANGE= "orientation_change"
    GYRO_CHANGE="gyro_change"
    SCRIPT_VARIABLE_CHANGE="script_variable_change"
    BACKGROUND_CONTROL_STATE_CHANGE="background_control_state_change"
    TIMER_TICK="timer_tick"
    FATAL_ERROR="fatal_error"
    # Temporarily, for background processes to be triggered.
    MCU_TICK="mcu_tick"


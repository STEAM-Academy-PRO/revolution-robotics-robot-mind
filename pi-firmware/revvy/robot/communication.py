from abc import ABC, abstractmethod


class RobotCommunicationInterface(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def set_periodic_control_msg_cb(self, callback):
        pass

    @abstractmethod
    def set_joystick_action_cb(self, callback):
        pass

    @abstractmethod
    def set_validate_config_req_cb(self, callback):
        pass


    @abstractmethod
    def on_connection_changed(self, callback):
        pass


    #----------------------------------------------

    @abstractmethod
    def update_session_id(self, id):
        pass

    @abstractmethod
    def set_validation_result(self, success, motors, sensors):
        pass

    @abstractmethod
    def update_orientation(self, vector_orientation):
        pass

    @abstractmethod
    def update_gyro(self, vector_list):
        pass

    @abstractmethod
    def update_motor(self, id, power, speed, pos):
        pass

    @abstractmethod
    def update_sensor(self, raw_value):
        pass

    @abstractmethod
    def update_script_variable(self, script_variables):
        pass

    @abstractmethod
    def update_state_control(self, control_state):
        pass

    @abstractmethod
    def update_timer(self, time):
        pass

    @abstractmethod
    def update_characteristic(self, name, value):
        pass

    @abstractmethod
    def battery(self, name):
        pass

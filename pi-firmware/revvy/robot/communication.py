from abc import ABC, abstractmethod


class RobotCommunicationInterface(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def update_session_id(self, id):
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
    def update_battery(self, bat_main, charger_status, motor, motor_present):
        pass

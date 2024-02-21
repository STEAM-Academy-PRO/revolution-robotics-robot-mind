from abc import abstractmethod
from enum import Enum
from revvy.mcu.rrrc_control import RevvyControl
from revvy.robot.ports.common import DriverConfig, PortHandler, PortDriver, PortInstance

from revvy.utils.awaiter import Awaiter, AwaiterState, Awaiter


class MotorConstants:
    """A bunch of constants that blockly can pass to motor APIs"""

    DIRECTION_FWD = 0
    DIRECTION_BACK = 1
    DIRECTION_LEFT = 2
    DIRECTION_RIGHT = 3

    UNIT_ROT = 0
    UNIT_SEC = 1
    UNIT_DEG = 2
    UNIT_TURN_ANGLE = 3

    UNIT_SPEED_RPM = 0
    UNIT_SPEED_PWR = 1

    ACTION_STOP_AND_HOLD = 0
    ACTION_RELEASE = 1


class MotorStatus(Enum):
    NORMAL = 0
    BLOCKED = 1
    GOAL_REACHED = 2


class MotorPortDriver(PortDriver):
    def __init__(self, port: PortInstance, driver_name: str):
        super().__init__(port, driver_name)

        port.interface.set_motor_port_type(port.id, port._supported[driver_name])

    @property
    @abstractmethod
    def status(self) -> MotorStatus:
        pass

    @property
    @abstractmethod
    def speed(self):
        pass

    @property
    @abstractmethod
    def pos(self):
        pass

    @property
    @abstractmethod
    def power(self):
        pass

    @abstractmethod
    def set_speed(self, speed, power_limit=None):
        pass

    @abstractmethod
    def set_position(
        self, position: int, speed_limit=None, power_limit=None, pos_type="absolute"
    ) -> Awaiter:
        pass

    @abstractmethod
    def set_power(self, power):
        pass

    @abstractmethod
    def update_status(self, data):
        pass

    @abstractmethod
    def stop(self, action: int = MotorConstants.ACTION_RELEASE):
        pass


class MotorPortHandler(PortHandler[MotorPortDriver]):
    def __init__(self, interface: RevvyControl):
        port_amount = interface.get_motor_port_amount()
        port_types = interface.get_motor_port_types()

        super().__init__(
            "Motor",
            interface,
            DriverConfig(driver=NullMotor, config={}),
            port_amount,
            port_types,
            interface.set_motor_port_type,
        )


class NullMotor(MotorPortDriver):
    def __init__(self, port: PortInstance, config):
        super().__init__(port, "NotConfigured")

    @property
    def status(self) -> MotorStatus:
        return MotorStatus.NORMAL

    @property
    def speed(self):
        return 0

    @property
    def pos(self):
        return 0

    @property
    def power(self):
        return 0

    def set_speed(self, speed, power_limit=None):
        pass

    def set_position(
        self, position: int, speed_limit=None, power_limit=None, pos_type="absolute"
    ) -> Awaiter:
        return Awaiter.from_state(AwaiterState.FINISHED)

    def set_power(self, power):
        pass

    def update_status(self, data):
        pass

    def stop(self, action: int = MotorConstants.ACTION_RELEASE):
        pass

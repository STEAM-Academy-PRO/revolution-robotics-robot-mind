from abc import abstractmethod
from enum import Enum
from typing import Optional
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


class MotorPositionKind(Enum):
    RELATIVE = 0
    ABSOLUTE = 1


class MotorPortDriver(PortDriver):
    def __init__(self, port: PortInstance, driver_name: str):
        super().__init__(port, driver_name, "Motor")

        port.interface.set_motor_port_type(port.id, port._supported[driver_name])

    @property
    @abstractmethod
    def status(self) -> MotorStatus: ...

    @property
    @abstractmethod
    def active_request_id(self) -> int:
        """Returns the request ID that was last read back from the MCU."""

    @property
    @abstractmethod
    def speed(self) -> float: ...

    @property
    @abstractmethod
    def pos(
        self,
    ) -> int:
        """Returns the current position of the motor in degrees."""

    @property
    @abstractmethod
    def power(self) -> int: ...

    @abstractmethod
    def set_speed(self, speed: float, power_limit: Optional[float] = None): ...

    @abstractmethod
    def set_position(
        self,
        position: int,
        speed_limit=None,
        power_limit=None,
        pos_type: MotorPositionKind = MotorPositionKind.ABSOLUTE,
    ) -> Awaiter: ...

    @abstractmethod
    def set_power(self, power: int): ...

    @abstractmethod
    def stop(self, action: int = MotorConstants.ACTION_RELEASE): ...


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
    def active_request_id(self) -> int:
        return 0

    @property
    def speed(self) -> float:
        return 0

    @property
    def pos(self) -> int:
        return 0

    @property
    def power(self) -> int:
        return 0

    def set_speed(self, speed: float, power_limit: Optional[float] = None):
        pass

    def set_position(
        self,
        position: int,
        speed_limit: Optional[float] = None,
        power_limit: Optional[float] = None,
        pos_type=MotorPositionKind.ABSOLUTE,
    ) -> Awaiter:
        return Awaiter(AwaiterState.FINISHED)

    def set_power(self, power):
        pass

    def update_status(self, data: bytes):
        pass

    def stop(self, action: int = MotorConstants.ACTION_RELEASE):
        pass

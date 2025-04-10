import unittest
from unittest.mock import call

from mock import Mock
from revvy.robot.configurations import DriverConfig, Motors

from revvy.robot.ports.common import PortInstance
from revvy.robot.ports.motors.base import (
    MotorConstants,
    MotorPortDriver,
    MotorPortHandler,
    MotorStatus,
)
from revvy.robot.ports.motors.dc_motor import DcMotorController
from revvy.utils.awaiter import Awaiter, AwaiterState
from revvy.utils.logger import get_logger


class TestDriver(MotorPortDriver):
    def __init__(self, port: "PortInstance", _):
        super(TestDriver, self).__init__(port, "Test")

    @property
    def status(self) -> MotorStatus:
        return MotorStatus.NORMAL

    @property
    def active_request_id(self) -> int:
        return 0

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
        return Awaiter(AwaiterState.FINISHED)

    def set_power(self, power):
        pass

    def update_status(self, data):
        pass

    def stop(self, action=MotorConstants.ACTION_RELEASE):
        pass


class TestMotorPortHandler(unittest.TestCase):
    def test_constructor_reads_port_amount_and_types(self):
        mock_control = Mock()
        mock_control.get_motor_port_amount = Mock(return_value=6)
        mock_control.get_motor_port_types = Mock(return_value={"NotConfigured": 0, "DcMotor": 1})

        ports = MotorPortHandler(mock_control)

        self.assertEqual(1, mock_control.get_motor_port_amount.call_count)
        self.assertEqual(1, mock_control.get_motor_port_types.call_count)

        self.assertEqual(6, ports.port_count)

    def test_motor_ports_are_indexed_from_zero(self):
        mock_control = Mock()
        mock_control.get_motor_port_amount = Mock(return_value=6)
        mock_control.get_motor_port_types = Mock(return_value={"NotConfigured": 0})

        ports = MotorPortHandler(mock_control)

        self.assertIs(PortInstance, type(ports[0]))
        self.assertIs(PortInstance, type(ports[1]))
        self.assertIs(PortInstance, type(ports[2]))
        self.assertIs(PortInstance, type(ports[3]))
        self.assertIs(PortInstance, type(ports[4]))
        self.assertIs(PortInstance, type(ports[5]))
        self.assertRaises(IndexError, lambda: ports[6])

    def test_configure_raises_error_if_driver_is_not_supported_in_mcu(self):
        mock_control = Mock()
        mock_control.get_motor_port_amount = Mock(return_value=6)
        mock_control.get_motor_port_types = Mock(return_value={"NotConfigured": 0})
        mock_control.set_motor_port_type = Mock()

        ports = MotorPortHandler(mock_control)

        self.assertIs(PortInstance, type(ports[1]))
        self.assertEqual(6, mock_control.set_motor_port_type.call_count)

        self.assertRaises(
            KeyError, lambda: ports[1].configure(DriverConfig(driver=TestDriver, config={}))
        )
        self.assertEqual(6, mock_control.set_motor_port_type.call_count)


class TestDcMotorDriver(unittest.TestCase):
    config = Motors.RevvyMotor.config

    @staticmethod
    def create_port():

        port = Mock()
        port.id = 2
        port._supported = {"NotConfigured": 0, "DcMotor": 1}
        port.interface = Mock()
        port.interface.set_motor_port_config = Mock()
        port.interface.set_motor_port_control_value = Mock()
        port.interface.set_motor_port_control_value.return_value = b"\x00"
        port.interface.get_motor_position = Mock()
        port.log = get_logger("MockPort")

        return port

    def test_constructor_does_not_send_configuration(self):
        port = self.create_port()

        DcMotorController(port, self.config)

        self.assertEqual(1, port.interface.set_motor_port_config.call_count)
        (passed_port_id, passed_config) = port.interface.set_motor_port_config.call_args[0]

        self.assertEqual(2, passed_port_id)

        configs = 4 + (20 + 20 + 5) + 20 + 4 + 4 + 4
        linearity_table = 6 * 8
        expected_bytes = configs + linearity_table
        self.assertEqual(expected_bytes, len(passed_config))

    def test_set_pos_changes_read_value(self):
        port = self.create_port()
        driver = DcMotorController(port, self.config)

        self.assertEqual(0, driver.pos)
        driver.pos = 5
        self.assertEqual(5, driver.pos)
        driver.pos = 0
        self.assertEqual(0, driver.pos)

    def test_set_pos_changes_command_value(self):
        port = self.create_port()
        driver = DcMotorController(port, self.config)

        driver.set_position(10)
        driver.pos = 5
        driver.set_position(10)
        driver.pos = 15
        driver.set_position(10)

        self.assertEqual(
            call(bytes([42, 2, 10, 0, 0, 0])),  # move to 10
            port.interface.set_motor_port_control_value.call_args_list[0],
        )
        # cancellation of movement
        self.assertEqual(
            call(bytes([18, 0, 0])), port.interface.set_motor_port_control_value.call_args_list[1]
        )
        self.assertEqual(
            call(bytes([42, 2, 5, 0, 0, 0])),  # move to 5
            port.interface.set_motor_port_control_value.call_args_list[2],
        )
        # cancellation of movement
        self.assertEqual(
            call(bytes([18, 0, 0])),  # cancel
            port.interface.set_motor_port_control_value.call_args_list[3],
        )
        self.assertEqual(
            call(bytes([42, 2, 251, 255, 255, 255])),  # move to -5
            port.interface.set_motor_port_control_value.call_args_list[4],
        )

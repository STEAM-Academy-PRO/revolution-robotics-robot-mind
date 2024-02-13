
import unittest
from unittest.mock import call

from mock import Mock

from revvy.robot.ports.common import PortInstance, PortDriver
from revvy.robot.ports.motors.base import MotorPortHandler
from revvy.robot.ports.motors.dc_motor import DcMotorController


class TestDriver(PortDriver):
    def __init__(self, port: 'PortInstance', _):
        super(TestDriver, self).__init__(port, "Test")

    def on_port_type_set(self):
        pass

    def update_status(self):
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

    def test_motor_ports_are_indexed_from_one(self):
        mock_control = Mock()
        mock_control.get_motor_port_amount = Mock(return_value=6)
        mock_control.get_motor_port_types = Mock(return_value={"NotConfigured": 0})

        ports = MotorPortHandler(mock_control)

        self.assertRaises(IndexError, lambda: ports[0])
        self.assertIs(PortInstance, type(ports[1]))
        self.assertIs(PortInstance, type(ports[2]))
        self.assertIs(PortInstance, type(ports[3]))
        self.assertIs(PortInstance, type(ports[4]))
        self.assertIs(PortInstance, type(ports[5]))
        self.assertIs(PortInstance, type(ports[6]))
        self.assertRaises(IndexError, lambda: ports[7])

    def test_configure_raises_error_if_driver_is_not_supported_in_mcu(self):
        mock_control = Mock()
        mock_control.get_motor_port_amount = Mock(return_value=6)
        mock_control.get_motor_port_types = Mock(return_value={"NotConfigured": 0})
        mock_control.set_motor_port_type = Mock()

        ports = MotorPortHandler(mock_control)

        self.assertIs(PortInstance, type(ports[1]))
        self.assertEqual(0, mock_control.set_motor_port_type.call_count)

        self.assertRaises(KeyError, lambda: ports[1].configure({"driver": TestDriver, "config": {}}))
        self.assertEqual(0, mock_control.set_motor_port_type.call_count)


class TestDcMotorDriver(unittest.TestCase):
    config = {
        'speed_controller':    [1 / 25, 0.3, 0, -100, 100],
        'position_controller': [10, 0, 0, -900, 900],
        'acceleration_limits': [10, 10],
        'encoder_resolution':  12,
        'gear_ratio': 64.8,
        'max_current': 1.0,
        'linearity': {0: 0, 1: 1}
    }

    @staticmethod
    def create_port():

        port = Mock()
        port.id = 3
        port.interface = Mock()
        port.interface.set_motor_port_config = Mock()
        port.interface.set_motor_port_control_value = Mock()
        port.interface.get_motor_position = Mock()

        return port

    def test_constructor_does_not_send_configuration(self):
        port = self.create_port()

        driver = DcMotorController(port, self.config)

        self.assertEqual(0, port.interface.set_motor_port_config.call_count)

        driver.on_port_type_set()
        (passed_port_id, passed_config) = port.interface.set_motor_port_config.call_args[0]

        self.assertEqual(3, passed_port_id)
        self.assertEqual(56 + 2 * 8, len(passed_config))

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

        self.assertEqual(call((42, 2, 10, 0, 0, 0)),  # move to 10
                         port.interface.set_motor_port_control_value.call_args_list[0])
        # cancellation of movement
        self.assertEqual(call((18, 0, 0)),
                         port.interface.set_motor_port_control_value.call_args_list[1])
        self.assertEqual(call((42, 2, 5, 0, 0, 0)),  # move to 5
                         port.interface.set_motor_port_control_value.call_args_list[2])
        # cancellation of movement
        self.assertEqual(call((18, 0, 0)),  # cancel
                         port.interface.set_motor_port_control_value.call_args_list[3])
        self.assertEqual(call((42, 2, 251, 255, 255, 255)),  # move to -5
                         port.interface.set_motor_port_control_value.call_args_list[4])

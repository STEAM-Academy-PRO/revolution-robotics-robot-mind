# SPDX-License-Identifier: GPL-3.0-only

import unittest

from mock import Mock

from revvy.robot.ports.common import PortInstance
from revvy.robot.ports.motor import create_motor_port_handler, DcMotorController


class TestMotorPortHandler(unittest.TestCase):
    def test_constructor_reads_port_amount_and_types(self):
        mock_control = Mock()
        mock_control.get_motor_port_amount = Mock(return_value=6)
        mock_control.get_motor_port_types = Mock(return_value={"NotConfigured": 0, "DcMotor": 1})

        ports = create_motor_port_handler(mock_control)

        self.assertEqual(1, mock_control.get_motor_port_amount.call_count)
        self.assertEqual(1, mock_control.get_motor_port_types.call_count)

        self.assertEqual(6, ports.port_count)

    def test_motor_ports_are_indexed_from_one(self):
        mock_control = Mock()
        mock_control.get_motor_port_amount = Mock(return_value=6)
        mock_control.get_motor_port_types = Mock(return_value={"NotConfigured": 0})

        ports = create_motor_port_handler(mock_control)

        self.assertRaises(KeyError, lambda: ports[0])
        self.assertIs(PortInstance, type(ports[1]))
        self.assertIs(PortInstance, type(ports[2]))
        self.assertIs(PortInstance, type(ports[3]))
        self.assertIs(PortInstance, type(ports[4]))
        self.assertIs(PortInstance, type(ports[5]))
        self.assertIs(PortInstance, type(ports[6]))
        self.assertRaises(KeyError, lambda: ports[7])

    def test_configure_raises_error_if_driver_is_not_supported_in_mcu(self):
        mock_control = Mock()
        mock_control.get_motor_port_amount = Mock(return_value=6)
        mock_control.get_motor_port_types = Mock(return_value={"NotConfigured": 0})
        mock_control.set_motor_port_type = Mock()

        ports = create_motor_port_handler(mock_control)

        self.assertIs(PortInstance, type(ports[1]))
        self.assertEqual(0, mock_control.set_motor_port_type.call_count)

        self.assertRaises(KeyError, lambda: ports[1].configure({"driver": "Test", "config": {}}))
        self.assertEqual(0, mock_control.set_motor_port_type.call_count)


class TestDcMotorDriver(unittest.TestCase):
    config = {
        'speed_controller':    [1 / 25, 0.3, 0, -100, 100],
        'position_controller': [10, 0, 0, -900, 900],
        'acceleration_limits': [10, 10],
        'encoder_resolution':  1168
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
        self.assertEqual(50, len(passed_config))

    def test_set_power_sends_port_idx_and_command_and_data(self):
        port = self.create_port()

        dc = DcMotorController(port, self.config)

        dc.set_power(20)

        method = port.interface.set_motor_port_control_value
        (passed_port_id, passed_control) = method.call_args[0]

        self.assertEqual(1, method.call_count)
        self.assertEqual(3, passed_port_id)
        self.assertEqual(2, len(passed_control))
        self.assertEqual(0, passed_control[0])  # command id
        self.assertEqual(20, passed_control[1])  # power

import unittest

from mock import Mock
from revvy.robot.configurations import DriverConfig

from revvy.robot.ports.common import PortInstance
from revvy.robot.ports.sensors.base import SensorPortDriver, SensorPortHandler


class NonExistentDriver(SensorPortDriver):
    def __init__(self, port, config):
        super().__init__(port, "NonExistentDriver")

    def convert_sensor_value(self, raw):
        return raw


class TestSensorPortHandler(unittest.TestCase):
    def test_constructor_reads_port_amount_and_types(self):
        mock_control = Mock()
        mock_control.get_sensor_port_amount = Mock(return_value=4)
        mock_control.get_sensor_port_types = Mock(
            return_value={"NotConfigured": 0, "BumperSwitch": 1, "HC_SR04": 2}
        )

        ports = SensorPortHandler(mock_control)

        self.assertEqual(1, mock_control.get_sensor_port_amount.call_count)
        self.assertEqual(1, mock_control.get_sensor_port_types.call_count)

        self.assertEqual(4, ports.port_count)

    def test_motor_ports_are_indexed_from_one(self):
        mock_control = Mock()
        mock_control.get_sensor_port_amount = Mock(return_value=4)
        mock_control.get_sensor_port_types = Mock(return_value={"NotConfigured": 0})

        ports = SensorPortHandler(mock_control)

        self.assertRaises(IndexError, lambda: ports[0])
        self.assertIs(PortInstance, type(ports[1]))
        self.assertIs(PortInstance, type(ports[2]))
        self.assertIs(PortInstance, type(ports[3]))
        self.assertIs(PortInstance, type(ports[4]))
        self.assertRaises(IndexError, lambda: ports[5])

    def test_configure_raises_error_if_driver_is_not_supported_in_mcu(self):
        mock_control = Mock()
        mock_control.get_sensor_port_amount = Mock(return_value=4)
        mock_control.get_sensor_port_types = Mock(return_value={"NotConfigured": 0})
        mock_control.set_sensor_port_type = Mock()

        ports = SensorPortHandler(mock_control)

        self.assertIs(PortInstance, type(ports[1]))
        self.assertEqual(4, mock_control.set_sensor_port_type.call_count)

        self.assertRaises(
            KeyError, lambda: ports[1].configure(DriverConfig(driver=NonExistentDriver, config={}))
        )
        self.assertEqual(4, mock_control.set_sensor_port_type.call_count)

    def test_unconfiguring_not_configured_port_does_nothing(self):
        mock_control = Mock()
        mock_control.get_sensor_port_amount = Mock(return_value=6)
        mock_control.get_sensor_port_types = Mock(return_value={"NotConfigured": 0})
        mock_control.set_sensor_port_type = Mock()

        ports = SensorPortHandler(mock_control)

        self.assertIs(PortInstance, type(ports[1]))
        self.assertEqual(0, mock_control.set_motor_port_type.call_count)

        ports[1].configure(None)
        self.assertEqual(0, mock_control.set_motor_port_type.call_count)


def create_port():

    port = Mock()
    port.id = 3
    port.interface = Mock()
    port.interface.get_sensor_port_value = Mock()

    return port

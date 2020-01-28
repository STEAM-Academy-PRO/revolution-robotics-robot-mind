# SPDX-License-Identifier: GPL-3.0-only

import unittest

from revvy.mcu.commands import *
from revvy.mcu.rrrc_transport import Response


class MockTransport:
    def __init__(self, responses):
        self._responses = responses
        self._command_count = 0
        self._commands = []

    def send_command(self, command, payload=None) -> Response:
        response = self._responses[self._command_count]
        self._command_count += 1
        self._commands.append((command, payload))
        return response

    @property
    def command_count(self):
        return self._command_count

    @property
    def commands(self):
        return self._commands


class MockCommand(Command):
    @property
    def command_id(self):
        return 2


# noinspection PyTypeChecker
class TestCommand(unittest.TestCase):
    def test_not_overwritten_command_id_raises_error(self):
        self.assertRaises(NotImplementedError, lambda: Command(None))

    def test_default_call_does_not_accept_arguments(self):
        c = MockCommand(None)
        self.assertRaises(NotImplementedError, lambda: c([1, 2, 3]))

    def test_call_sends_command(self):
        mock_transport = MockTransport([Response(ResponseStatus.Ok, [])])
        c = MockCommand(mock_transport)
        self.assertEqual(0, mock_transport.command_count)
        c()
        self.assertEqual(1, mock_transport.command_count)
        self.assertEqual((2, b''), mock_transport.commands[0])

    def test_default_command_raises_when_response_has_payload(self):
        mock_transport = MockTransport([Response(ResponseStatus.Ok, [1])])
        c = MockCommand(mock_transport)
        self.assertRaises(NotImplementedError, c)
        # assert that command was sent
        self.assertEqual(1, mock_transport.command_count)

    def test_command_raises_when_response_is_not_ok(self):
        mock_transport = MockTransport([
            Response(ResponseStatus.Error_UnknownCommand, []),
            Response(ResponseStatus.Error_UnknownOperation, []),
            Response(ResponseStatus.Error_CommandError, []),
            Response(ResponseStatus.Error_CommandIntegrityError, []),
            Response(ResponseStatus.Error_InternalError, []),
            Response(ResponseStatus.Error_InvalidOperation, []),
            Response(ResponseStatus.Error_PayloadIntegrityError, []),
            Response(ResponseStatus.Error_PayloadLengthError, []),
        ])

        c = MockCommand(mock_transport)

        self.assertRaises(UnknownCommandError, c)
        self.assertRaises(ValueError, c)
        self.assertRaises(ValueError, c)
        self.assertRaises(ValueError, c)
        self.assertRaises(ValueError, c)
        self.assertRaises(ValueError, c)
        self.assertRaises(ValueError, c)
        self.assertRaises(ValueError, c)


# noinspection PyTypeChecker
class TestCommandTypes(unittest.TestCase):
    def test_ping_has_no_payload_and_return_value(self):
        mock_transport = MockTransport([Response(ResponseStatus.Ok, [])])
        ping = PingCommand(mock_transport)
        self.assertIsNone(ping())
        self.assertEqual(b'', mock_transport.commands[0][1])

    def test_hardware_version_returns_a_string(self):
        mock_transport = MockTransport([
            Response(ResponseStatus.Ok, b'0.1'),
            Response(ResponseStatus.Ok, b'v0.1')
        ])
        hw = ReadHardwareVersionCommand(mock_transport)
        self.assertEqual(Version("0.1"), hw())
        self.assertEqual(None, hw())

    def test_firmware_version_returns_a_string(self):
        mock_transport = MockTransport([
            Response(ResponseStatus.Ok, b'0.1-r5'),
            Response(ResponseStatus.Ok, b'v0.1-r5')
        ])
        fw = ReadFirmwareVersionCommand(mock_transport)
        self.assertEqual(Version("0.1-r5"), fw())
        self.assertEqual(None, fw())

    def test_set_master_status_payload_is_one_byte(self):
        mock_transport = MockTransport([
            Response(ResponseStatus.Ok, []),
            Response(ResponseStatus.Ok, [1]),
        ])
        set_status = SetMasterStatusCommand(mock_transport)

        self.assertIsNone(set_status(3))
        self.assertListEqual([3], list(mock_transport.commands[0][1]))

        # unexpected payload byte
        self.assertRaises(NotImplementedError, lambda: set_status(3))

    def test_set_bluetooth_status_payload_is_one_byte(self):
        mock_transport = MockTransport([
            Response(ResponseStatus.Ok, []),
            Response(ResponseStatus.Ok, [1]),
        ])
        set_status = SetBluetoothStatusCommand(mock_transport)

        self.assertIsNone(set_status(3))
        self.assertListEqual([3], list(mock_transport.commands[0][1]))

        # unexpected payload byte
        self.assertRaises(NotImplementedError, lambda: set_status(3))

    def test_read_motor_port_types_returns_a_dict(self):
        mock_transport = MockTransport([
            Response(ResponseStatus.Ok, b''),  # no strings
            Response(ResponseStatus.Ok, b'\x01\x06foobar'),  # one string
            Response(ResponseStatus.Ok, b'\x01\x06foobar\x03\x04hola'),  # multiple strings
        ])
        read_types = ReadMotorPortTypesCommand(mock_transport)

        self.assertFalse(read_types())
        self.assertDictEqual({'foobar': 1}, read_types())
        self.assertDictEqual({'foobar': 1, 'hola': 3}, read_types())

    def test_read_sensor_port_types_returns_a_dict(self):
        mock_transport = MockTransport([
            Response(ResponseStatus.Ok, b''),  # no strings
            Response(ResponseStatus.Ok, b'\x01\x06foobar'),  # one string
            Response(ResponseStatus.Ok, b'\x01\x06foobar\x03\x04hola'),  # multiple strings
        ])
        read_types = ReadSensorPortTypesCommand(mock_transport)

        self.assertFalse(read_types())
        self.assertDictEqual({'foobar': 1}, read_types())
        self.assertDictEqual({'foobar': 1, 'hola': 3}, read_types())

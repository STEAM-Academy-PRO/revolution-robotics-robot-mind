# SPDX-License-Identifier: GPL-3.0-only

import binascii
import unittest

import mock

from revvy.mcu.rrrc_transport import Command, crc7, RevvyTransport, RevvyTransportInterface, ResponseHeader


class TestCommand(unittest.TestCase):
    def test_first_byte_is_opcode(self):
        ch = Command.start(5, bytes())
        self.assertEqual(0, ch.get_bytes()[0])

        ch = Command.get_result(5)
        self.assertEqual(2, ch.get_bytes()[0])

        ch = Command.cancel(5)
        self.assertEqual(3, ch.get_bytes()[0])

    def test_max_payload_length_is_255(self):
        ch = Command.start(5, b'\x00'*25)
        self.assertEqual(6 + 25, len(ch.get_bytes()))
        self.assertEqual(25, ch.get_bytes()[2])

        ch = Command.start(5, b'\x00'*255)
        self.assertEqual(6 + 255, len(ch.get_bytes()))
        self.assertEqual(255, ch.get_bytes()[2])

        self.assertRaises(ValueError, lambda: Command.start(5, b'\x00' * 256))

    def test_empty_payload_header_is_ffff(self):
        ch = Command.start(5, bytes())

        self.assertEqual(bytes([0xFF, 0xFF]), ch.get_bytes()[3:5])

    def test_header_checksum_is_calculated_using_crc7(self):
        ch = Command.start(5, bytes())
        expected_checksum = crc7([Command.OpStart, 5, 0, 0xFF, 0xFF], 0xFF)

        self.assertEqual(expected_checksum, ch.get_bytes()[5])

    def test_header_checksum_includes_payload(self):
        ch = Command.start(5, b'\x01\x02\x03')

        payload_checksum = bytes(binascii.crc_hqx(bytes([1, 2, 3]), 0xFFFF).to_bytes(2, byteorder='little'))

        checksum_if_payload_ffff = crc7([Command.OpStart, 5, 0, 0xFF, 0xFF], 0xFF)
        expected_checksum = crc7([Command.OpStart, 5, 0, *payload_checksum], 0xFF)

        self.assertNotEqual(checksum_if_payload_ffff, ch.get_bytes()[5])
        self.assertNotEqual(expected_checksum, ch.get_bytes()[5])


class MockInterface(RevvyTransportInterface):

    def __init__(self, read_responses):
        self._responses = list(map(bytes, read_responses))
        self._writes = []
        self._reads = []
        self._counter = 0

    def read(self, length):
        idx = len(self._reads)
        self._reads.append((self._counter, length))
        self._counter += 1
        return self._responses[idx][0:length]

    def write(self, data):
        self._writes.append((self._counter, data))
        self._counter += 1


class TestRevvyTransport(unittest.TestCase):
    def test_only_one_write_if_immediate_successful_response(self):
        mock_interface = MockInterface([
            [ResponseHeader.Status_Ok, 0, 0xFF, 0xFF, 117]  # immediately respond with success
        ])
        rt = RevvyTransport(mock_interface)
        response = rt.send_command(10, [8, 9])  # some ping-type command
        self.assertEqual(2, mock_interface._counter)  # write, read header, no data
        self.assertEqual(1, len(mock_interface._writes))
        self.assertEqual(1, len(mock_interface._reads))
        self.assertEqual(0, mock_interface._writes[0][0])  # write happened first
        self.assertEqual(1, mock_interface._reads[0][0])  # read happened second
        self.assertEqual(Command.start(10, b'\x08\x09').get_bytes(), mock_interface._writes[0][1])
        self.assertEqual(ResponseHeader.Status_Ok, response.status)
        self.assertEqual(0, len(response.payload))

    def test_retry_reading_after_busy_response(self):
        mock_interface = MockInterface([
            [ResponseHeader.Status_Busy, 0, 0xFF, 0xFF, 118],
            [ResponseHeader.Status_Busy, 0, 0xFF, 0xFF, 118],
            [ResponseHeader.Status_Busy, 0, 0xFF, 0xFF, 118],
            [ResponseHeader.Status_Busy, 0, 0xFF, 0xFF, 118],
            [ResponseHeader.Status_Busy, 0, 0xFF, 0xFF, 118],
            [ResponseHeader.Status_Ok, 0, 0xFF, 0xFF, 117]  # finally respond with success
        ])
        rt = RevvyTransport(mock_interface)
        response = rt.send_command(10)  # some ping-type command
        self.assertEqual(1, len(mock_interface._writes))
        self.assertEqual(6, len(mock_interface._reads))
        self.assertEqual(0, mock_interface._writes[0][0])  # write happened first
        self.assertEqual(ResponseHeader.Status_Ok, response.status)
        self.assertEqual(0, len(response.payload))

    def test_raise_error_if_header_changes_before_reading_data(self):
        mock_interface = MockInterface([
            [ResponseHeader.Status_Ok, 2, 0xaf, 0x43, 121],
            [ResponseHeader.Status_Ok, 0, 0xFF, 0xFF, 117, 0, 0],  # different header when reading data
            [ResponseHeader.Status_Ok, 0, 0xFF, 0xFF, 117, 0, 0],  # read is retried 5 times
            [ResponseHeader.Status_Ok, 0, 0xFF, 0xFF, 117, 0, 0],
            [ResponseHeader.Status_Ok, 0, 0xFF, 0xFF, 117, 0, 0],
            [ResponseHeader.Status_Ok, 0, 0xFF, 0xFF, 117, 0, 0]
        ])
        rt = RevvyTransport(mock_interface)
        self.assertRaises(BrokenPipeError, lambda: rt.send_command(10))
        self.assertEqual(1, len(mock_interface._writes))
        self.assertEqual(6, len(mock_interface._reads))

    def test_return_response_if_header_changes_back_while_repeatedly_reading_data(self):
        mock_interface = MockInterface([
            [ResponseHeader.Status_Ok, 2, 0xaf, 0x43, 121],
            [ResponseHeader.Status_Ok, 0, 0xFF, 0xFF, 117, 0, 0],  # different header when reading data
            [ResponseHeader.Status_Ok, 0, 0xFF, 0xFF, 117, 0, 0],  # read is retried 5 times or until success
            [ResponseHeader.Status_Ok, 0, 0xFF, 0xFF, 117, 0, 0],
            [ResponseHeader.Status_Ok, 2, 0xaf, 0x43, 121, 0x0a, 0x0b]
        ])
        rt = RevvyTransport(mock_interface)
        response = rt.send_command(10)
        self.assertEqual(1, len(mock_interface._writes))
        self.assertEqual(5, len(mock_interface._reads))
        self.assertEqual(b'\x0a\x0b', response.payload)

    def test_data_header_is_read_before_full_response(self):
        mock_interface = MockInterface([
            [ResponseHeader.Status_Ok, 2, 0xaf, 0x43, 121],  # respond with header first
            [ResponseHeader.Status_Ok, 2, 0xaf, 0x43, 121, 0x0a, 0x0b]  # respond with success
        ])
        rt = RevvyTransport(mock_interface)
        response = rt.send_command(10)  # some ping-type command
        self.assertEqual(ResponseHeader.Status_Ok, response.status)
        self.assertEqual(2, len(mock_interface._reads))
        self.assertEqual(5, mock_interface._reads[0][1])
        self.assertEqual(7, mock_interface._reads[1][1])
        self.assertEqual(b'\x0a\x0b', response.payload)

    def test_header_read_is_repeated_if_integrity_check_fails(self):
        mock_interface = MockInterface([
            [ResponseHeader.Status_Ok, 2, 0xaf, 0x42, 121],  # respond with invalid header first
            [ResponseHeader.Status_Ok, 2, 0xaf, 0x43, 121],  # respond with header first
            [ResponseHeader.Status_Ok, 2, 0xaf, 0x43, 121, 0x0a, 0x0b]  # respond with success
        ])
        rt = RevvyTransport(mock_interface)
        response = rt.send_command(10)  # some ping-type command
        self.assertEqual(3, len(mock_interface._reads))
        self.assertEqual(ResponseHeader.Status_Ok, response.status)
        self.assertEqual(b'\x0a\x0b', response.payload)

    def test_data_read_is_repeated_if_header_integrity_check_fails(self):
        mock_interface = MockInterface([
            [ResponseHeader.Status_Ok, 2, 0xaf, 0x43, 121],  # respond with header first
            [ResponseHeader.Status_Ok, 2, 0x5f, 0x43, 121, 0x0a, 0x0b],  # respond with success, but invalid header
            [ResponseHeader.Status_Ok, 2, 0xaf, 0x43, 121, 0x0a, 0x0b]  # respond with success
        ])
        rt = RevvyTransport(mock_interface)
        response = rt.send_command(10)  # some ping-type command
        self.assertEqual(3, len(mock_interface._reads))
        self.assertEqual(ResponseHeader.Status_Ok, response.status)
        self.assertEqual(b'\x0a\x0b', response.payload)

    def test_data_read_is_repeated_if_payload_integrity_check_fails(self):
        mock_interface = MockInterface([
            [ResponseHeader.Status_Ok, 2, 0xaf, 0x43, 121],  # respond with header first
            [ResponseHeader.Status_Ok, 2, 0xaf, 0x43, 121, 0x0a, 0x0c],  # respond with success, but invalid payload
            [ResponseHeader.Status_Ok, 2, 0xaf, 0x43, 121, 0x0a, 0x0b]  # respond with success
        ])
        rt = RevvyTransport(mock_interface)
        response = rt.send_command(10)  # some ping-type command
        self.assertEqual(3, len(mock_interface._reads))
        self.assertEqual(ResponseHeader.Status_Ok, response.status)
        self.assertEqual(b'\x0a\x0b', response.payload)

    def test_pending_is_retried_with_get_result(self):
        mock_interface = MockInterface([
            [ResponseHeader.Status_Pending, 0, 0xff, 0xff, 115],
            [ResponseHeader.Status_Pending, 0, 0xff, 0xff, 115],
            [ResponseHeader.Status_Pending, 0, 0xff, 0xff, 115],
            [ResponseHeader.Status_Ok, 2, 0xaf, 0x43, 121],             # respond with header first
            [ResponseHeader.Status_Ok, 2, 0xaf, 0x43, 121, 0x0a, 0x0b]  # respond with success
        ])
        rt = RevvyTransport(mock_interface)
        response = rt.send_command(10)  # some ping-type command
        self.assertEqual(ResponseHeader.Status_Ok, response.status)
        self.assertEqual(4, len(mock_interface._writes))

        self.assertEqual(0, mock_interface._writes[0][0])
        self.assertEqual(Command.OpStart, mock_interface._writes[0][1][0])

        self.assertEqual(2, mock_interface._writes[1][0])
        self.assertEqual(Command.OpGetResult, mock_interface._writes[1][1][0])

        self.assertEqual(4, mock_interface._writes[2][0])
        self.assertEqual(Command.OpGetResult, mock_interface._writes[2][1][0])

        self.assertEqual(6, mock_interface._writes[3][0])
        self.assertEqual(Command.OpGetResult, mock_interface._writes[3][1][0])

        self.assertEqual(5, len(mock_interface._reads))
        self.assertEqual(b'\x0a\x0b', response.payload)

    def test_multiple_header_errors_raises_error(self):
        mock_interface = MockInterface([
            [ResponseHeader.Status_Ok, 2, 0x5f, 0x43, 121],  # respond with invalid header
            [ResponseHeader.Status_Ok, 2, 0x5f, 0x43, 121],  # respond with invalid header
            [ResponseHeader.Status_Ok, 2, 0x5f, 0x43, 121],  # respond with invalid header
            [ResponseHeader.Status_Ok, 2, 0x5f, 0x43, 121],  # respond with invalid header
            [ResponseHeader.Status_Ok, 2, 0x5f, 0x43, 121],  # respond with invalid header
        ])
        rt = RevvyTransport(mock_interface)
        self.assertRaises(BrokenPipeError, lambda: rt.send_command(10))

    def test_multiple_payload_errors_raises_error(self):
        mock_interface = MockInterface([
            [ResponseHeader.Status_Ok, 2, 0xaf, 0x43, 121],  # respond with header first
            [ResponseHeader.Status_Ok, 2, 0xaf, 0x43, 121, 0x0a, 0x0c],  # respond with success, but invalid payload
            [ResponseHeader.Status_Ok, 2, 0xaf, 0x43, 121, 0x0a, 0x0c],  # respond with success, but invalid payload
            [ResponseHeader.Status_Ok, 2, 0xaf, 0x43, 121, 0x0a, 0x0c],  # respond with success, but invalid payload
            [ResponseHeader.Status_Ok, 2, 0xaf, 0x43, 121, 0x0a, 0x0c],  # respond with success, but invalid payload
            [ResponseHeader.Status_Ok, 2, 0xaf, 0x43, 121, 0x0a, 0x0c],  # respond with success, but invalid payload
        ])
        rt = RevvyTransport(mock_interface)
        self.assertRaises(BrokenPipeError, lambda: rt.send_command(10))

    @mock.patch('time.time', mock.MagicMock(side_effect=[0, 1, 2, 3, 4, 5, 6]))
    def test_busy_response_can_timeout(self):
        mock_interface = MockInterface([
            [ResponseHeader.Status_Busy, 0, 0xFF, 0xFF, 118]
        ] * 10)
        rt = RevvyTransport(mock_interface)
        rt.timeout = 5
        self.assertEqual(ResponseHeader.Status_Error_Timeout, rt.send_command(10).status)
        self.assertLess(len(mock_interface._reads), 10)


class TestResponse(unittest.TestCase):
    def test_response_shorter_than_header_size_is_invalid(self):
        data = bytes([ResponseHeader.Status_Ok, 0, 0xFF, 0xFF])  # one byte short

        self.assertRaises(ValueError, lambda: ResponseHeader(data))
        ResponseHeader(bytes((*data, 117)))  # does not raise

    def test_response_header_with_wrong_checksum_is_invalid(self):
        data = bytes([ResponseHeader.Status_Ok, 0, 0xFF, 0xFF, 118])

        self.assertRaises(ValueError, lambda: ResponseHeader(data))

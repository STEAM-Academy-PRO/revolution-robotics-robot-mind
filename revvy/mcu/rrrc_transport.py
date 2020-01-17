# SPDX-License-Identifier: GPL-3.0-only

import struct
import binascii
from enum import Enum
from threading import Lock

from revvy.utils.functions import retry
from revvy.utils.stopwatch import Stopwatch

crc7_table = [
    0x00, 0x09, 0x12, 0x1b, 0x24, 0x2d, 0x36, 0x3f,
    0x48, 0x41, 0x5a, 0x53, 0x6c, 0x65, 0x7e, 0x77,
    0x19, 0x10, 0x0b, 0x02, 0x3d, 0x34, 0x2f, 0x26,
    0x51, 0x58, 0x43, 0x4a, 0x75, 0x7c, 0x67, 0x6e,
    0x32, 0x3b, 0x20, 0x29, 0x16, 0x1f, 0x04, 0x0d,
    0x7a, 0x73, 0x68, 0x61, 0x5e, 0x57, 0x4c, 0x45,
    0x2b, 0x22, 0x39, 0x30, 0x0f, 0x06, 0x1d, 0x14,
    0x63, 0x6a, 0x71, 0x78, 0x47, 0x4e, 0x55, 0x5c,
    0x64, 0x6d, 0x76, 0x7f, 0x40, 0x49, 0x52, 0x5b,
    0x2c, 0x25, 0x3e, 0x37, 0x08, 0x01, 0x1a, 0x13,
    0x7d, 0x74, 0x6f, 0x66, 0x59, 0x50, 0x4b, 0x42,
    0x35, 0x3c, 0x27, 0x2e, 0x11, 0x18, 0x03, 0x0a,
    0x56, 0x5f, 0x44, 0x4d, 0x72, 0x7b, 0x60, 0x69,
    0x1e, 0x17, 0x0c, 0x05, 0x3a, 0x33, 0x28, 0x21,
    0x4f, 0x46, 0x5d, 0x54, 0x6b, 0x62, 0x79, 0x70,
    0x07, 0x0e, 0x15, 0x1c, 0x23, 0x2a, 0x31, 0x38,
    0x41, 0x48, 0x53, 0x5a, 0x65, 0x6c, 0x77, 0x7e,
    0x09, 0x00, 0x1b, 0x12, 0x2d, 0x24, 0x3f, 0x36,
    0x58, 0x51, 0x4a, 0x43, 0x7c, 0x75, 0x6e, 0x67,
    0x10, 0x19, 0x02, 0x0b, 0x34, 0x3d, 0x26, 0x2f,
    0x73, 0x7a, 0x61, 0x68, 0x57, 0x5e, 0x45, 0x4c,
    0x3b, 0x32, 0x29, 0x20, 0x1f, 0x16, 0x0d, 0x04,
    0x6a, 0x63, 0x78, 0x71, 0x4e, 0x47, 0x5c, 0x55,
    0x22, 0x2b, 0x30, 0x39, 0x06, 0x0f, 0x14, 0x1d,
    0x25, 0x2c, 0x37, 0x3e, 0x01, 0x08, 0x13, 0x1a,
    0x6d, 0x64, 0x7f, 0x76, 0x49, 0x40, 0x5b, 0x52,
    0x3c, 0x35, 0x2e, 0x27, 0x18, 0x11, 0x0a, 0x03,
    0x74, 0x7d, 0x66, 0x6f, 0x50, 0x59, 0x42, 0x4b,
    0x17, 0x1e, 0x05, 0x0c, 0x33, 0x3a, 0x21, 0x28,
    0x5f, 0x56, 0x4d, 0x44, 0x7b, 0x72, 0x69, 0x60,
    0x0e, 0x07, 0x1c, 0x15, 0x2a, 0x23, 0x38, 0x31,
    0x46, 0x4f, 0x54, 0x5d, 0x62, 0x6b, 0x70, 0x79]


def crc7(data, crc=0xFF):
    """
    >>> crc7(b'foobar')
    16
    """
    for b in data:
        crc = crc7_table[(b ^ (crc << 1) & 0xFF)]
    return crc


class TransportException(Exception):
    pass


class RevvyTransportInterface:
    def read(self, length): raise NotImplementedError()
    def write(self, data): raise NotImplementedError()


class Command:
    OpStart = 0
    OpRestart = 1
    OpGetResult = 2
    OpCancel = 3

    def __init__(self, op, command, payload=b''):
        payload_length = len(payload)
        if payload_length > 255:
            raise ValueError('Payload is too long ({} bytes, 255 allowed)'.format(payload_length))

        pl = bytearray(6 + payload_length)
        pl[6:] = payload

        payload_checksum = binascii.crc_hqx(pl[6:], 0xFFFF)

        # fill header
        pl[0:5] = op, command, payload_length, *payload_checksum.to_bytes(2, byteorder='little')

        # calculate header checksum
        pl[5] = crc7(pl[0:5], 0xFF)

        self._payload = pl

    def get_bytes(self):
        return self._payload

    @classmethod
    def start(cls, command, payload: bytes) -> 'Command':
        return cls(cls.OpStart, command, payload)

    @classmethod
    def get_result(cls, command) -> 'Command':
        return cls(cls.OpGetResult, command)

    @classmethod
    def cancel(cls, command) -> 'Command':
        return cls(cls.OpCancel, command)


class ResponseStatus(Enum):
    Ok = 0
    Busy = 1
    Pending = 2

    Error_UnknownOperation = 3
    Error_InvalidOperation = 4
    Error_CommandIntegrityError = 5
    Error_PayloadIntegrityError = 6
    Error_PayloadLengthError = 7
    Error_UnknownCommand = 8
    Error_CommandError = 9
    Error_InternalError = 10

    # errors not sent by MCU
    Error_Timeout = 11


class ResponseHeader:
    length = 5

    def __init__(self, data: bytes):
        if len(data) < ResponseHeader.length:
            raise ValueError('Header too short')

        self._raw = data[0:self.length-1]
        checksum = crc7(self._raw)
        if checksum != data[self.length-1]:
            raise ValueError('Header checksum mismatch')

        (status, self._payload_length, self._payload_checksum) = struct.unpack('<bbH', self._raw)
        self._status = ResponseStatus(status)

    def validate_payload(self, payload):
        return self._payload_checksum == binascii.crc_hqx(payload, 0xFFFF)

    def __eq__(self, o: 'ResponseHeader') -> bool:
        return o._raw == self._raw

    @property
    def status(self) -> ResponseStatus:
        return self._status

    @property
    def payload_length(self):
        return self._payload_length


class Response:
    def __init__(self, status: ResponseStatus, payload: bytes):
        self._status = status
        self._payload = payload

    @property
    def status(self):
        return self._status

    @property
    def payload(self) -> bytes:
        return self._payload


class RevvyTransport:
    _mutex = Lock()  # we only have a single I2C interface
    timeout = 5  # [seconds] how long the slave is allowed to respond with "busy"

    def __init__(self, transport: RevvyTransportInterface):
        self._transport = transport
        self._stopwatch = Stopwatch()

    def send_command(self, command, payload=b'') -> Response:
        """
        Send a command and get the result.

        This function waits for commands to finish processing, so execution time depends on the MCU.
        The function detects integrity errors and retries incorrect writes and reads.

        @param command:
        @param payload:
        @return:
        """
        with self._mutex:
            # create commands in advance, they can be reused in case of an error
            command_start = Command.start(command, payload)
            command_get_result = Command.get_result(command)

            try:
                # once a command gets through and a valid response is read, this loop will exit
                while True:  # assume that integrity error is random and not caused by implementation differences
                    # send command and read back status
                    header = self._send_command(command_start)

                    # wait for command execution to finish
                    while header.status == ResponseStatus.Pending:
                        header = self._send_command(command_get_result)

                    # check result
                    # return a result even in case of an error, except when we know we have to resend
                    if header.status != ResponseStatus.Error_CommandIntegrityError:
                        response_payload = self._read_payload(header)
                        return Response(header.status, response_payload)
            except TimeoutError:
                return Response(ResponseStatus.Error_Timeout, b'')

    def _read_response_header(self, retries=5) -> ResponseHeader:
        """
        Read header part of response message

        Header is always 5 bytes long and it contains the length of the variable payload

        @param retries: How many times the read can be retried in case an error happens
        @return: The header data
        """

        def _read_response_header_once():
            header_bytes = self._transport.read(ResponseHeader.length)

            return ResponseHeader(header_bytes)

        header = retry(_read_response_header_once, retries)

        if not header:
            raise BrokenPipeError('Read response header: Retry limit reached')
        return header

    def _read_payload(self, header, retries=5) -> bytes:
        """
        Read the rest of the response

        Reading always starts with the header (nondestructive) so we need to read the header and verify that
        we receive the same header as before

        @param header: The expected header
        @param retries: How many times the read can be retried in case an error happens
        @return: The payload bytes
        """
        if header.payload_length == 0:
            return b''

        def _read_payload_once():
            # read header and payload
            response_bytes = self._transport.read(header.length + header.payload_length)

            # make sure we read the same response data we expect
            response_header = ResponseHeader(response_bytes)
            if not header == response_header:
                raise ValueError('Read payload: Unexpected header received')

            # make sure data is intact
            payload_bytes = response_bytes[ResponseHeader.length:]
            if not header.validate_payload(payload_bytes):
                raise ValueError('Read payload: payload contents invalid')

            return payload_bytes

        payload = retry(_read_payload_once, retries)

        if not payload:
            raise BrokenPipeError('Read payload: Retry limit reached')

        return payload

    def _send_command(self, command: Command) -> ResponseHeader:
        """
        Send a command and return the response header

        This function waits for the slave MCU to finish processing the command and returns if it is done or the
        timeout defined in the class header elapses.

        @param command: The command to send
        @return: The response header
        """
        self._transport.write(command.get_bytes())
        self._stopwatch.reset()
        while self.timeout == 0 or self._stopwatch.elapsed < self.timeout:
            response = self._read_response_header()
            if response.status != ResponseStatus.Busy:
                return response
        raise TimeoutError

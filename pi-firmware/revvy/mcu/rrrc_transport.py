import struct
import binascii
from enum import Enum
from threading import Lock
from typing import NamedTuple
import time

from revvy.utils.functions import retry
from revvy.utils.logger import LogLevel, get_logger
from revvy.utils.stopwatch import Stopwatch

log = get_logger("rrrc_transport")

crc7_table = (
    0x00,
    0x09,
    0x12,
    0x1B,
    0x24,
    0x2D,
    0x36,
    0x3F,
    0x48,
    0x41,
    0x5A,
    0x53,
    0x6C,
    0x65,
    0x7E,
    0x77,
    0x19,
    0x10,
    0x0B,
    0x02,
    0x3D,
    0x34,
    0x2F,
    0x26,
    0x51,
    0x58,
    0x43,
    0x4A,
    0x75,
    0x7C,
    0x67,
    0x6E,
    0x32,
    0x3B,
    0x20,
    0x29,
    0x16,
    0x1F,
    0x04,
    0x0D,
    0x7A,
    0x73,
    0x68,
    0x61,
    0x5E,
    0x57,
    0x4C,
    0x45,
    0x2B,
    0x22,
    0x39,
    0x30,
    0x0F,
    0x06,
    0x1D,
    0x14,
    0x63,
    0x6A,
    0x71,
    0x78,
    0x47,
    0x4E,
    0x55,
    0x5C,
    0x64,
    0x6D,
    0x76,
    0x7F,
    0x40,
    0x49,
    0x52,
    0x5B,
    0x2C,
    0x25,
    0x3E,
    0x37,
    0x08,
    0x01,
    0x1A,
    0x13,
    0x7D,
    0x74,
    0x6F,
    0x66,
    0x59,
    0x50,
    0x4B,
    0x42,
    0x35,
    0x3C,
    0x27,
    0x2E,
    0x11,
    0x18,
    0x03,
    0x0A,
    0x56,
    0x5F,
    0x44,
    0x4D,
    0x72,
    0x7B,
    0x60,
    0x69,
    0x1E,
    0x17,
    0x0C,
    0x05,
    0x3A,
    0x33,
    0x28,
    0x21,
    0x4F,
    0x46,
    0x5D,
    0x54,
    0x6B,
    0x62,
    0x79,
    0x70,
    0x07,
    0x0E,
    0x15,
    0x1C,
    0x23,
    0x2A,
    0x31,
    0x38,
    0x41,
    0x48,
    0x53,
    0x5A,
    0x65,
    0x6C,
    0x77,
    0x7E,
    0x09,
    0x00,
    0x1B,
    0x12,
    0x2D,
    0x24,
    0x3F,
    0x36,
    0x58,
    0x51,
    0x4A,
    0x43,
    0x7C,
    0x75,
    0x6E,
    0x67,
    0x10,
    0x19,
    0x02,
    0x0B,
    0x34,
    0x3D,
    0x26,
    0x2F,
    0x73,
    0x7A,
    0x61,
    0x68,
    0x57,
    0x5E,
    0x45,
    0x4C,
    0x3B,
    0x32,
    0x29,
    0x20,
    0x1F,
    0x16,
    0x0D,
    0x04,
    0x6A,
    0x63,
    0x78,
    0x71,
    0x4E,
    0x47,
    0x5C,
    0x55,
    0x22,
    0x2B,
    0x30,
    0x39,
    0x06,
    0x0F,
    0x14,
    0x1D,
    0x25,
    0x2C,
    0x37,
    0x3E,
    0x01,
    0x08,
    0x13,
    0x1A,
    0x6D,
    0x64,
    0x7F,
    0x76,
    0x49,
    0x40,
    0x5B,
    0x52,
    0x3C,
    0x35,
    0x2E,
    0x27,
    0x18,
    0x11,
    0x0A,
    0x03,
    0x74,
    0x7D,
    0x66,
    0x6F,
    0x50,
    0x59,
    0x42,
    0x4B,
    0x17,
    0x1E,
    0x05,
    0x0C,
    0x33,
    0x3A,
    0x21,
    0x28,
    0x5F,
    0x56,
    0x4D,
    0x44,
    0x7B,
    0x72,
    0x69,
    0x60,
    0x0E,
    0x07,
    0x1C,
    0x15,
    0x2A,
    0x23,
    0x38,
    0x31,
    0x46,
    0x4F,
    0x54,
    0x5D,
    0x62,
    0x6B,
    0x70,
    0x79,
)


def crc7(data, crc=0xFF):
    """
    >>> crc7(b'foobar')
    16
    """
    for b in data:
        crc = crc7_table[b ^ ((crc << 1) & 0xFF)]
    return crc


class TransportException(Exception):
    pass


class RevvyTransportInterface:
    def read(self, length):
        raise NotImplementedError()

    def write(self, data):
        raise NotImplementedError()


class Command:
    OpStart = 0
    OpRestart = 1
    OpGetResult = 2
    OpCancel = 3

    @staticmethod
    def create(op, command, payload=b""):
        payload_length = len(payload)
        if payload_length > 255:
            raise ValueError(f"Payload is too long ({payload_length} bytes, 255 allowed)")

        pl = bytearray(6 + payload_length)

        if payload:
            pl[6:] = payload
            payload_checksum = binascii.crc_hqx(pl[6:], 0xFFFF)
            high_byte, low_byte = divmod(payload_checksum, 256)  # get bytes of unsigned short
        else:
            high_byte = low_byte = 0xFF

        # fill header
        pl[0:5] = op, command, payload_length, low_byte, high_byte

        # calculate header checksum
        pl[5] = crc7(pl[0:5])

        return pl

    @staticmethod
    def start(command, payload: bytes):
        """
        >>> Command.start(2, b'')
        bytearray(b'\\x00\\x02\\x00\\xff\\xffQ')
        """
        return Command.create(Command.OpStart, command, payload)

    @staticmethod
    def get_result(command):
        """
        >>> Command.get_result(2)
        bytearray(b'\\x02\\x02\\x00\\xff\\xff=')
        """
        return Command.create(Command.OpGetResult, command)

    @staticmethod
    def cancel(command):
        return Command.create(Command.OpCancel, command)


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


class ResponseHeader(NamedTuple):
    status: ResponseStatus
    payload_length: int
    payload_checksum: int
    raw: bytes

    @staticmethod
    def create(data: bytes):
        try:
            if not ResponseHeader.is_valid(data):
                raise ValueError("Header checksum error")

            header_bytes = data[0:4]
            status, _payload_length, _payload_checksum = struct.unpack("<BBH", header_bytes)
            return ResponseHeader(
                status=ResponseStatus(status),
                payload_length=_payload_length,
                payload_checksum=_payload_checksum,
                raw=header_bytes,
            )
        except IndexError as e:
            raise ValueError("Header too short") from e

    @staticmethod
    def is_valid(data: bytes):
        """Checks if a communication header is valid"""
        if data == None:
            return False
        header_bytes = data[0:4]
        if crc7(header_bytes) != data[4]:
            # log(f"Header Check CRC error: {str(data)} !=  {str(header_bytes)}", LogLevel.WARNING)
            return False
        return True

    def validate_payload(self, payload):
        return self.payload_checksum == binascii.crc_hqx(payload, 0xFFFF)

    def is_same_as(self, response_header):
        return self.raw == response_header


class Response(NamedTuple):
    status: ResponseStatus
    payload: bytes


class RevvyTransport:
    _mutex = Lock()  # we only have a single I2C interface
    timeout = 75  # [seconds] how long the slave is allowed to respond with "busy"

    def __init__(self, transport: RevvyTransportInterface):
        self._transport = transport
        self._stopwatch = Stopwatch()
        self.retry_reads = 100  # 100 seems like an excessive value

    def send_command(self, command, payload=b"", get_result_delay=None) -> Response:
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
            command_get_result = None

            try:
                # once a command gets through and a valid response is read, this loop will exit
                while (
                    True
                ):  # assume that integrity error is random and not caused by implementation differences
                    # send command and read back status
                    header = self._send_command(command_start)

                    # wait for command execution to finish
                    if header.status == ResponseStatus.Pending:
                        # lazily create GetResult command
                        if not command_get_result:
                            command_get_result = Command.get_result(command)

                        if get_result_delay:
                            time.sleep(get_result_delay)
                        header = self._send_command(command_get_result)
                        while header.status == ResponseStatus.Pending:
                            if get_result_delay:
                                time.sleep(get_result_delay)
                            header = self._send_command(command_get_result)

                    # check result
                    # return a result even in case of an error, except when we know we have to resend
                    if header.status != ResponseStatus.Error_CommandIntegrityError:
                        response_payload = self._read_payload(header, retries=self.retry_reads)
                        # print("command: ", command, "response_payload:", response_payload)
                        return Response(header.status, response_payload)
            except TimeoutError:
                return Response(ResponseStatus.Error_Timeout, b"")

    def _read_response_header(self, retries=5) -> ResponseHeader:
        """
        Read header part of response message

        Header is always 5 bytes long and it contains the length of the variable payload

        @param retries: How many times the read can be retried in case an error happens
        @return: The header data
        """

        def _read_response_header_once():
            header_bytes = self._transport.read(5)

            return ResponseHeader.create(header_bytes)

        header = retry(_read_response_header_once, retries, lambda e: None)

        if not header:
            # log("Connection lost with the board, retry limit reached!", LogLevel.ERROR)
            raise BrokenPipeError("Read response header error")

        return header

    def _read_payload(self, header: ResponseHeader, retries=5) -> bytes:
        """
        Read the rest of the response

        Reading always starts with the header (nondestructive) so we need to read the header and verify that
        we receive the same header as before

        @param header: The expected header
        @param retries: How many times the read can be retried in case an error happens
        @return: The payload bytes
        """
        if header.payload_length == 0:
            return b""

        def _read_payload_once():
            # read header and payload
            response_bytes = self._transport.read(5 + header.payload_length)
            response_header, response_payload = (
                response_bytes[0:4],
                response_bytes[5:],
            )  # skip checksum byte

            # make sure we read the same response data we expect
            if not header.is_same_as(response_header):
                # raise ValueError('Read payload: Unexpected header received')
                return 0

            # make sure data is intact
            if not header.validate_payload(response_payload):
                # raise ValueError('Read payload: payload contents invalid')
                return 0

            return response_payload

        payload = retry(_read_payload_once, retries)

        if not payload:
            # log("Connection lost with the board, retry limit reached!", LogLevel.ERROR)
            raise BrokenPipeError("Read payload: Retry limit reached")

        return payload

    def _send_command(self, command: bytes) -> ResponseHeader:
        """
        Send a command and return the response header

        This function waits for the slave MCU to finish processing the command and returns if it is done or the
        timeout defined in the class header elapses.

        @param command: The command bytes to send
        @return: The response header
        """
        self._transport.write(command)
        self._stopwatch.reset()
        while self._stopwatch.elapsed < self.timeout:
            response = self._read_response_header(retries=100)
            if response is not None and response.status != ResponseStatus.Busy:
                return response
        raise TimeoutError

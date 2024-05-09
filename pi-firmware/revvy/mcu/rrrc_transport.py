from abc import ABC, abstractmethod
import struct
import binascii
from enum import Enum
from threading import Lock
import time
from typing import NamedTuple

from revvy.utils.functions import retry
from revvy.utils.logger import LogLevel, get_logger
from revvy.utils.stopwatch import Stopwatch

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


def crc7(data, crc: int = 0xFF) -> int:
    """
    >>> crc7(b'foobar')
    16
    """
    for b in data:
        crc = crc7_table[b ^ ((crc << 1) & 0xFF)]
    return crc


class TransportException(Exception):
    pass


class RevvyTransportInterface(ABC):
    @abstractmethod
    def read(self, length: int) -> bytes:
        pass

    @abstractmethod
    def write(self, data: bytes):
        pass


class Command:
    OpStart = 0
    # OpRestart removed
    OpGetResult = 2
    # OpCancel removed

    @staticmethod
    def create(op, command: int, payload: bytes = b"") -> bytearray:
        if command > 255:
            raise ValueError(f"Command id must be a single byte")
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
    def start(command: int, payload: bytes) -> bytearray:
        """
        >>> Command.start(2, b'')
        bytearray(b'\\x00\\x02\\x00\\xff\\xffQ')
        """
        return Command.create(Command.OpStart, command, payload)

    @staticmethod
    def get_result(command: int) -> bytearray:
        """
        >>> Command.get_result(2)
        bytearray(b'\\x02\\x02\\x00\\xff\\xff=')
        """
        return Command.create(Command.OpGetResult, command)


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


response_header = struct.Struct("<BBH")


class ResponseHeader(NamedTuple):
    status: ResponseStatus
    payload_length: int
    payload_checksum: int
    raw: bytes

    @staticmethod
    def create(data: bytes) -> "ResponseHeader":
        if len(data) < 5:
            raise ValueError(f"Header too short. Received {len(data)} bytes, expected at least 5")

        if not ResponseHeader.is_valid(data):
            raise ValueError(f"Header checksum error. Data = {list(data)}")

        header_bytes = data[0:4]
        status, payload_length, payload_checksum = response_header.unpack(header_bytes)
        return ResponseHeader(
            status=ResponseStatus(status),
            payload_length=payload_length,
            payload_checksum=payload_checksum,
            raw=header_bytes,
        )

    @staticmethod
    def is_valid(data: bytes):
        """Checks if a communication header is valid"""
        header_bytes = data[0:4]
        if crc7(header_bytes) != data[4]:
            # log(f"Header Check CRC error: {str(data)} !=  {str(header_bytes)}", LogLevel.WARNING)
            return False
        return True

    def validate_payload(self, payload) -> bool:
        return self.payload_checksum == binascii.crc_hqx(payload, 0xFFFF)


class Response(NamedTuple):
    status: ResponseStatus
    payload: bytes


class RevvyTransport:
    _transaction_mutex = Lock()  # Ensures that write-read pairs are not interrupted
    timeout = 5  # [seconds] how long the MCU is allowed to respond with "busy" or no response
    retry = 50  # FIXME: 50 seems like an excessive value
    retry_sleep_threshold = 20  # FIXME: This is a hack to work around an RPi Zero v1 issue that may prevent firmware updates from succeedin.

    def __init__(self, transport: RevvyTransportInterface):
        self._transport = transport
        self._stopwatch = Stopwatch()
        self.log = get_logger("rrrc_transport")

    def send_command(
        self, command: int, payload: bytes = b"", exec_timeout: float = 5.0
    ) -> Response:
        """
        Send a command and get the result.

        This function waits for commands to finish processing, so execution time depends on the MCU.
        The function detects integrity errors and retries incorrect writes and reads.

        @param command: the command id
        @param payload: command-specific payload
        @param exec_timeout: deadline for the command to finish processing, in seconds

        @return: The response
        """

        timeout = Stopwatch()

        command_start = Command.start(command, payload)

        try:
            # retry on bit errors
            # assume that integrity error is random and not caused by implementation differences
            # once a command gets through and a valid response is read, this loop will exit
            while True:
                # send command and read back status
                response = self._send_command(command_start)

                # wait for command execution to finish
                if response.status == ResponseStatus.Pending:
                    command_get_result = Command.get_result(command)

                    while True:
                        response = self._send_command(command_get_result)
                        if response.status != ResponseStatus.Pending:
                            # execution done, stop polling
                            break
                        if timeout.elapsed > exec_timeout:
                            return Response(ResponseStatus.Error_Timeout, b"")

                return Response(response.status, response.payload)
        except TimeoutError:
            return Response(ResponseStatus.Error_Timeout, b"")

    def _read_response(self) -> Response:
        """
        Read response message

        Header is always 5 bytes long and it contains the length of the variable payload.
        We read this header part first, then re-read the header and payload together to verify
        that the data is intact.

        @param retries: How many times the read can be retried in case an error happens
        @return: The header data
        """

        response_header = None
        exception = None
        for i in range(self.retry):
            try:
                header_bytes = self._transport.read(5)
                response_header = ResponseHeader.create(header_bytes)
                break
            except Exception as e:
                exception = e
                # if we're struggling to read the header, allow some time for the MCU to catch up.
                if i > self.retry_sleep_threshold:
                    time.sleep(0.01)

        if not response_header:
            self.log("Error reading response header: retry limit reached!", LogLevel.ERROR)
            raise BrokenPipeError(f"Read response header error: {exception}")

        # At this point we have read the response header and we know the command has
        # finished processing. We can now read the payload and return the result.
        payload = self._read_payload(response_header)

        return Response(response_header.status, payload)

    def _read_payload(self, header: ResponseHeader) -> bytes:
        """
        Read the rest of the response

        Reading always starts with the header (nondestructive) so we need to read the header and
        verify that we receive the same header as before

        @param header: The expected header
        @return: The payload bytes
        """
        if header.payload_length == 0:
            return b""

        def _read_payload_once() -> bytes:
            # read header and payload
            response_bytes = self._transport.read(5 + header.payload_length)
            response_header, response_payload = (
                response_bytes[0:4],
                response_bytes[5:],
            )  # skip checksum byte

            # make sure we read the same response data we expect
            if header.raw != response_header:
                return bytes()

            # make sure data is intact
            if not header.validate_payload(response_payload):
                return bytes()

            return response_payload

        payload = retry(_read_payload_once, self.retry)

        if not payload:
            self.log("Error reading response payload: retry limit reached!", LogLevel.ERROR)
            raise BrokenPipeError("Read payload: Retry limit reached")

        return payload

    def _send_command(self, command: bytes) -> Response:
        """
        Writes command (as in, Start or GetResult) bytes and return the response header. If the
        response contains a payload, the firmware can re-read it using `_read_payload`.

        This function waits for the MCU to finish processing the command and returns if it is
        done or the timeout defined in the class header elapses.

        @param command: The command bytes to send
        @return: The response header
        """

        self._stopwatch.reset()

        resend_command = True
        while resend_command and self._stopwatch.elapsed < self.timeout:
            # We need to ensure that we read the response to our written command. This mutex ensures
            # that we don't send a new command before the response to the previous one is read.
            with self._transaction_mutex:
                self._transport.write(command)
                resend_command = False

                while self._stopwatch.elapsed < self.timeout:
                    response = self._read_response()
                    # Busy means the MCU is not ready for this command yet and we should retry later.
                    if response.status == ResponseStatus.Busy:
                        continue  # retry reading the header
                    elif (
                        response.status == ResponseStatus.Error_CommandIntegrityError
                        or response.status == ResponseStatus.Error_PayloadIntegrityError
                    ):
                        resend_command = True
                        break  # exit reading loop to retry sending the command
                    else:
                        # we got a response to a command, so we can exit
                        if response.status != ResponseStatus.Ok:
                            self.log(f"response.status: {response.status}", LogLevel.DEBUG)

                        return response
        raise TimeoutError

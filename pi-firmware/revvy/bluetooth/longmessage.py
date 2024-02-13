
### Send and receive long messages via bluetooth.


import io
import os
import tarfile
import shutil
import threading
import traceback
import hashlib
import struct

from contextlib import suppress
from functools import partial
from json import JSONDecodeError
from typing import NamedTuple

from revvy.utils.file_storage import StorageInterface, StorageError
from revvy.utils.functions import split
from revvy.utils.logger import LogLevel, get_logger
from revvy.utils.progress_indicator import ProgressIndicator
from revvy.utils.functions import str_to_func

from revvy.robot.led_ring import RingLed
from revvy.robot.status import RobotStatus
from revvy.robot_manager import RevvyStatusCode, RobotManager
from revvy.robot_config import empty_robot_config, RobotConfig, ConfigError

from revvy.scripting.runtime import ScriptDescriptor, ScriptEvent
from revvy.utils.reverse_map_constant_name import get_constant_name



def hex2byte(h):
    return int(h, 16)


def hexdigest2bytes(hexdigest):
    """
    >>> hexdigest2bytes("aabbcc")
    b'\\xaa\\xbb\\xcc'
    >>> hexdigest2bytes("ABCDEF")
    b'\\xab\\xcd\\xef'
    >>> hexdigest2bytes("ABCD0F")
    b'\\xab\\xcd\\x0f'
    """
    return bytes(map(hex2byte, split(hexdigest, 2)))


def bytes2hexdigest(hash_bytes):
    """
    >>> bytes2hexdigest(b'\\xaa\\xbb\\xcc')
    'aabbcc'
    >>> bytes2hexdigest(b'\\xAB\\xCD\\xEF')
    'abcdef'
    >>> bytes2hexdigest(b'\\xAB\\xCD\\x0F')
    'abcd0f'
    """
    return "".join('{0:0>2x}'.format(byte) for byte in hash_bytes)


class LongMessageStatus:
    UNUSED = 0
    UPLOAD = 1
    READY = 3
    VALIDATION_ERROR = 4


class LongMessageStatusInfo(NamedTuple):
    status: int
    md5: bytes
    length: int


UnusedLongMessageStatusInfo = LongMessageStatusInfo(LongMessageStatus.UNUSED, b'', 0)
ValidationErrorLongMessageStatusInfo = LongMessageStatusInfo(LongMessageStatus.VALIDATION_ERROR, b'', 0)


class LongMessageType:
    FIRMWARE_DATA = 1
    FRAMEWORK_DATA = 2
    CONFIGURATION_DATA = 3
    TEST_KIT = 4
    ASSET_DATA = 5
    MAX = 6

    PermanentMessages = [FIRMWARE_DATA, FRAMEWORK_DATA, ASSET_DATA]

    @staticmethod
    def validate(long_message_type):
        if not (0 < long_message_type < LongMessageType.MAX):
            raise LongMessageError(f"Invalid long message type {long_message_type}")


class MessageType:
    SELECT_LONG_MESSAGE_TYPE = 0
    INIT_TRANSFER = 1
    UPLOAD_MESSAGE = 2
    FINALIZE_MESSAGE = 3


class LongMessageError(Exception):
    pass


class ReceivedLongMessage:
    """Helper class for building long messages"""

    def __init__(self, message_type, md5: str, size=0):
        self.message_type = message_type
        self.md5 = md5
        self.total_chunks = size
        self.received_chunks = 0
        self.data = bytearray()
        self._md5calc = hashlib.md5()
        self._size_known = size != 0

    def append_data(self, data):
        self.received_chunks += 1
        self.data += data
        self._md5calc.update(data)

    @property
    def is_valid(self):
        """Returns true if the uploaded data matches the predefined md5 checksum."""
        if self._size_known:
            if self.received_chunks != self.total_chunks:
                return False

        md5computed = self._md5calc.hexdigest()

        return md5computed == self.md5


class LongMessageStorage:
    """Store long messages using the given storage class, with extra validation"""

    def __init__(self, storage: StorageInterface, temp_storage: StorageInterface):
        self._storage = storage
        self._temp_storage = temp_storage
        self._log = get_logger('LongMessageStorage')

    def _get_storage(self, message_type):
        return self._storage if message_type in LongMessageType.PermanentMessages else self._temp_storage

    def read_status(self, long_message_type) -> LongMessageStatusInfo:
        """Return status with triplet of (LongMessageStatus, md5-hexdigest, length). Last two fields might be None)."""
        self._log("read_status")
        LongMessageType.validate(long_message_type)
        try:
            storage = self._get_storage(long_message_type)
            data = storage.read_metadata(long_message_type)
            return LongMessageStatusInfo(LongMessageStatus.READY, hexdigest2bytes(data['md5']), data['length'])

        except (StorageError, JSONDecodeError):
            return UnusedLongMessageStatusInfo

    def set_long_message(self, message: ReceivedLongMessage):
        self._log("set_long_message")
        LongMessageType.validate(message.message_type)
        storage = self._get_storage(message.message_type)
        storage.write(message.message_type, message.data, md5=message.md5)

    def get_long_message(self, long_message_type):
        self._log("get_long_message")
        storage = self._get_storage(long_message_type)
        return storage.read(long_message_type)


class LongMessageHandler:
    """Implements the long message writer/status reader protocol"""

    STATUS_IDLE = 0
    STATUS_READ = 1
    STATUS_WRITE = 2
    STATUS_INVALID = 3

    def __init__(self, long_message_storage: LongMessageStorage):
        self._long_message_storage = long_message_storage
        self._long_message_type = None
        self._status = LongMessageHandler.STATUS_IDLE
        self._current_message = None
        self._message_updated_callback = None
        self._upload_started_callback = None
        self._upload_progress_callback = None
        self._upload_finished_callback = None
        self._log = get_logger('LongMessageHandler')

    def on_message_updated(self, callback):
        self._message_updated_callback = callback

    def on_upload_started(self, callback):
        self._upload_started_callback = callback

    def on_upload_progress(self, callback):
        self._upload_progress_callback = callback

    def on_upload_finished(self, callback):
        self._upload_finished_callback = callback

    def read_status(self) -> LongMessageStatusInfo:
        # self._log("read_status")

        if self._status == LongMessageHandler.STATUS_IDLE:
            return UnusedLongMessageStatusInfo

        if self._status == LongMessageHandler.STATUS_READ:
            return self._long_message_storage.read_status(self._long_message_type)

        if self._status == LongMessageHandler.STATUS_INVALID:
            self._log("read_status_invalid!")
            return ValidationErrorLongMessageStatusInfo

        assert self._status == LongMessageHandler.STATUS_WRITE
        return LongMessageStatusInfo(
            LongMessageStatus.UPLOAD,
            hexdigest2bytes(self._current_message.md5),
            len(self._current_message.data))

    def select_long_message_type(self, long_message_type):
        if self._status == LongMessageHandler.STATUS_WRITE:
            upload_finished_callback = self._upload_finished_callback
            if upload_finished_callback:
                upload_finished_callback(self._current_message)

        self._log(f"select_long_message_type: {get_constant_name(long_message_type, LongMessageType)}")
        LongMessageType.validate(long_message_type)
        self._long_message_type = long_message_type
        self._status = LongMessageHandler.STATUS_READ

        self._current_message = None

    def init_transfer(self, md5: str, size=0):
        self._log("init_transfer")

        if self._status == LongMessageHandler.STATUS_WRITE:
            upload_finished_callback = self._upload_finished_callback
            if upload_finished_callback:
                upload_finished_callback(self._current_message)

        if self._status == LongMessageHandler.STATUS_IDLE:
            raise LongMessageError("init-transfer needs to be called after select_long_message_type")

        self._status = LongMessageHandler.STATUS_WRITE
        self._current_message = ReceivedLongMessage(self._long_message_type, md5, size)

        upload_started_callback = self._upload_started_callback
        if upload_started_callback:
            upload_started_callback(self._current_message)

    def upload_message(self, data):
        self._log(f"upload_message ({len(data)} bytes)")

        if self._status != LongMessageHandler.STATUS_WRITE:
            raise LongMessageError("init-transfer needs to be called before upload_message")

        self._current_message.append_data(data)
        upload_progress_callback = self._upload_progress_callback
        if upload_progress_callback:
            upload_progress_callback(self._current_message)

    def finalize_message(self):
        self._log("finalize_message")

        if self._status == LongMessageHandler.STATUS_IDLE:
            raise LongMessageError("init-transfer needs to be called before finalize_message")

        updated_callback = self._message_updated_callback
        upload_finished_callback = self._upload_finished_callback

        if self._status == LongMessageHandler.STATUS_READ:
            # shortcut that activates a message which is already on the robot

            # observer must take care of verifying that there is actually a message
            if updated_callback:
                if self._current_message is None:
                    # load the stored message contents
                    message = self._long_message_storage.get_long_message(self._long_message_type)
                    info = self._long_message_storage.read_status(self._long_message_type)
                    self._current_message = ReceivedLongMessage(
                        self._long_message_type,
                        bytes2hexdigest(info.md5),
                        info.length)
                    self._current_message.append_data(message)

                updated_callback(self._current_message)

        elif self._status == LongMessageHandler.STATUS_WRITE:
            if upload_finished_callback:
                upload_finished_callback(self._current_message)

            if self._current_message.is_valid:
                self._long_message_storage.set_long_message(self._current_message)
                if updated_callback:
                    updated_callback(self._current_message)
                self._status = LongMessageHandler.STATUS_READ
            else:
                self._status = LongMessageHandler.STATUS_INVALID

        else:
            # INVALID status, finalize does nothing
            pass


class LongMessageProtocol:
    RESULT_SUCCESS = 0
    RESULT_INVALID_ATTRIBUTE_LENGTH = 1
    RESULT_UNLIKELY_ERROR = 2

    def __init__(self, handler: LongMessageHandler):
        self._handler = handler

    def handle_read(self):
        try:
            status = self._handler.read_status()
            if status.status in [LongMessageStatus.READY, LongMessageStatus.UPLOAD]:
                # a byte, a 16byte string and an unsigned long packed into a big endian array
                value = struct.pack('>b16sL', status.status, status.md5, status.length)
            else:
                value = bytes((status.status, ))

            return value
        except (IOError, TypeError, JSONDecodeError) as e:
            raise LongMessageError('Could not read long message') from e

    def handle_write(self, header, data):
        if header == MessageType.SELECT_LONG_MESSAGE_TYPE:
            if len(data) == 1:
                self._handler.select_long_message_type(data[0])
                result = LongMessageProtocol.RESULT_SUCCESS
            else:
                result = LongMessageProtocol.RESULT_INVALID_ATTRIBUTE_LENGTH

        elif header == MessageType.INIT_TRANSFER:
            if len(data) == 16:
                self._handler.init_transfer(bytes2hexdigest(data), 0)
                result = LongMessageProtocol.RESULT_SUCCESS
            elif len(data) == 20:
                self._handler.init_transfer(bytes2hexdigest(data[0:16]), int.from_bytes(data[16:20], byteorder='big'))
                result = LongMessageProtocol.RESULT_SUCCESS
            else:
                result = LongMessageProtocol.RESULT_INVALID_ATTRIBUTE_LENGTH

        elif header == MessageType.UPLOAD_MESSAGE:
            if len(data) > 0:
                self._handler.upload_message(data)
                result = LongMessageProtocol.RESULT_SUCCESS
            else:
                result = LongMessageProtocol.RESULT_INVALID_ATTRIBUTE_LENGTH

        elif header == MessageType.FINALIZE_MESSAGE:
            if len(data) == 0:
                self._handler.finalize_message()
                result = LongMessageProtocol.RESULT_SUCCESS
            else:
                result = LongMessageProtocol.RESULT_INVALID_ATTRIBUTE_LENGTH

        else:
            result = LongMessageProtocol.RESULT_UNLIKELY_ERROR

        return result



def extract_asset_longmessage(storage, asset_dir):
    """
    Extract the ASSET_DATA long message into a folder.

    After successfully extracting, store the checksum of the asset message in the .hash file.
    Skip extracting if the long message has the same checksum as stored in the folder.
    The folder will be deleted if exists before decompression.

    @param storage: the source where the asset data message is stored
    @param asset_dir: the destination directory
    """

    asset_status = storage.read_status(LongMessageType.ASSET_DATA)

    if asset_status.status == LongMessageStatus.READY:
        with suppress(Exception):
            with open(os.path.join(asset_dir, '.hash'), 'r') as asset_hash_file:
                stored_hash = asset_hash_file.read()

            if stored_hash == asset_status.md5:
                return

        if os.path.isdir(asset_dir):
            shutil.rmtree(asset_dir)

        message_data = storage.get_long_message(LongMessageType.ASSET_DATA)
        with tarfile.open(fileobj=io.StringIO(message_data), mode="r|gz") as tar:
            tar.extractall(path=asset_dir)

        with open(os.path.join(asset_dir, '.hash'), 'w') as asset_hash_file:
            asset_hash_file.write(asset_status.md5)


# Moved from main file, cleanup pending.
class LongMessageImplementation:
    # TODO: this, together with the other long message classes is probably a lasagna worth simplifying
    def __init__(self, robot_manager: RobotManager, storage: LongMessageStorage, asset_dir):
        self._robot_manager = robot_manager
        self._asset_dir = asset_dir
        self._progress = None
        self._storage = storage

        self._log = get_logger("LongMessageImplementation")

    def on_upload_started(self, message: ReceivedLongMessage):
        """
            Visual indication that an upload has started.
            Requests LED ring change in the background.
        """

        message_type = message.message_type
        if message_type == LongMessageType.FRAMEWORK_DATA:
            self._progress = ProgressIndicator(self._robot_manager.robot.led, message.total_chunks, 0x00FF00, 0xFF00FF)
        else:
            self._progress = None
            # TODO: Is this the right place to change the robot's inner state?
            self._robot_manager.robot.status.robot_status = RobotStatus.Configuring

    def on_upload_progress(self, message: ReceivedLongMessage):
        """ Indicate long message download progress """
        if self._progress:
            if message.total_chunks == 0:
                # calculate approximate chunk count
                expected_size = 250000
                chunk_size = len(message.data) / message.received_chunks
                message.total_chunks = expected_size / chunk_size
                self._progress.end = message.total_chunks

            if message.total_chunks != 0:
                self._log(f'Progress: {message.received_chunks}/{message.total_chunks}')
                self._progress.update(message.received_chunks)

    def on_transmission_finished(self, message: ReceivedLongMessage):
        """
            Visual indication that an upload has finished.
            Requests LED ring change in the background.
        """

        message_type = message.message_type
        if message_type == LongMessageType.FRAMEWORK_DATA:
            if not message.is_valid:
                self._log('Firmware update cancelled')
                self._progress = None
                ### -------------------------------------------------------------------------!!!
                self._robot_manager.run_in_background(
                    partial(self._robot_manager.robot.led.start_animation, RingLed.BreathingGreen), 'LongMessageImplementation: on_transmission_finished: Firmware Update cancelled?')
        else:
            # Indicate exiting with the rainbow effect while the PI program exits.
            if self._progress:
                self._progress.show_indeterminate_loading_on_led_ring()

    def on_message_updated(self, message: ReceivedLongMessage):
        """
            When we received a long message, it's either a
            - TEST_KIT: for sensor tests or a
            - CONFIGURATION request (set up and enter play mode) or a
            - FRAMEWORK update that we need to install.
            - ASSET_DATA add new sound to the repertoire
        """
        message_type = message.message_type

        self._log(f'Received message: {get_constant_name(message_type, LongMessageType)}')

        # On the configuration screen, when selecting a sensor, there is a TEST button
        # on the right panel's bottom left, right next to DONE button. that is very hard to notice.
        # When that is pressed, custom test script is pushed down to the robot with this flag.

        if message_type == LongMessageType.TEST_KIT:

            test_script_source = message.data.decode()
            self._log(f'Running test script: \n{test_script_source}')

            script_descriptor = ScriptDescriptor("test_kit",
                        str_to_func(test_script_source), 0, source = test_script_source)

            self._robot_manager.robot_configure(empty_robot_config)

            def start_script():
                self._log("Starting new test script")
                ### -------------------------------------------------------------------------!!!
                ### TODO: Wrong params, how is this ever used?
                handle = self._robot_manager._scripts.add_script(script_descriptor)
                on_script_stopped_fn = partial(self._robot_manager.robot_configure, None)
                handle.on_stopped(on_script_stopped_fn)

                # start can't run in on_stopped handler because overwriting script causes deadlock
                self._robot_manager.run_in_background(handle.start, 'LongMessageImplementation: on_message_updated start_script()')

            self._robot_manager.robot_configure(empty_robot_config, start_script)

        elif message_type == LongMessageType.CONFIGURATION_DATA:
            message_data = message.data.decode()

            try:
                parsed_config = RobotConfig.from_string(message_data)
                self._robot_manager.robot_configure(parsed_config)
            except ConfigError:
                self._log(traceback.format_exc())

        elif message_type == LongMessageType.FRAMEWORK_DATA:
            # TODO: Eliminate calling robot status updates from the outside like this!
            self._robot_manager.robot.status.robot_status = RobotStatus.Updating
            self._progress.set_indeterminate()
            self._robot_manager.request_update()

        elif message_type == LongMessageType.ASSET_DATA:
            extract_asset_longmessage(self._storage, self._asset_dir)



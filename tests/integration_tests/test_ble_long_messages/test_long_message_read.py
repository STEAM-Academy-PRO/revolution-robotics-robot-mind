# SPDX-License-Identifier: GPL-3.0-only

import hashlib
import unittest

from revvy.bluetooth.longmessage import LongMessageStorage, LongMessageHandler, LongMessageProtocol, bytes2hexdigest, \
    MessageType, LongMessageType, LongMessageStatus
from revvy.utils.file_storage import MemoryStorage


class TestLongMessageRead(unittest.TestCase):
    def test_reading_unused_message_returns_zero(self):
        persistent = MemoryStorage()
        temp = MemoryStorage()

        storage = LongMessageStorage(persistent, temp)
        handler = LongMessageHandler(storage)
        ble = LongMessageProtocol(handler)

        ble.handle_write(0, [2])  # select long message 2
        result = ble.handle_read()

        # unused long message response is a 0 byte
        self.assertEqual(b'\x00', result)

    def test_read_returns_hash(self):
        persistent = MemoryStorage()
        persistent.write(2, b'abcd')

        md5_hash = hashlib.md5(b'abcd').hexdigest()

        temp = MemoryStorage()

        storage = LongMessageStorage(persistent, temp)
        handler = LongMessageHandler(storage)
        ble = LongMessageProtocol(handler)

        ble.handle_write(0, [2])  # select long message 2 (persistent)
        result = ble.handle_read()

        # reading a valid message returns its status, md5 hash and length
        self.assertEqual("03" + md5_hash + "00000004", bytes2hexdigest(result))

    def test_upload_message_with_one_byte_is_accepted(self):
        persistent = MemoryStorage()
        temp = MemoryStorage()

        storage = LongMessageStorage(persistent, temp)
        handler = LongMessageHandler(storage)
        ble = LongMessageProtocol(handler)

        ble.handle_write(0, [2])  # select long message 2
        ble.handle_write(1, bytes([0]*16))  # init
        self.assertEqual(LongMessageProtocol.RESULT_SUCCESS, ble.handle_write(MessageType.UPLOAD_MESSAGE, bytes([2])))

    def test_upload_is_only_valid_if_chunk_count_matches_expected(self):
        storage = LongMessageStorage(MemoryStorage(), MemoryStorage())
        chunks = [b'12345', b'1234568', b'98765432']

        checksum = hashlib.md5()
        for chunk in chunks:
            checksum.update(chunk)

        expected_md5 = checksum.hexdigest()

        handler = LongMessageHandler(storage)
        handler.select_long_message_type(LongMessageType.FIRMWARE_DATA)

        def run_update():
            for chunk in chunks:
                handler.upload_message(chunk)
            handler.finalize_message()

            return handler.read_status()

        handler.init_transfer(expected_md5, len(chunks))
        status = run_update()
        self.assertEqual(LongMessageStatus.READY, status.status)

        handler.init_transfer(expected_md5, 0)
        status = run_update()
        self.assertEqual(LongMessageStatus.READY, status.status)

        handler.init_transfer(expected_md5, len(chunks)+1)
        status = run_update()
        self.assertEqual(LongMessageStatus.VALIDATION_ERROR, status.status)

        handler.init_transfer(expected_md5, len(chunks)-1)
        status = run_update()
        self.assertEqual(LongMessageStatus.VALIDATION_ERROR, status.status)

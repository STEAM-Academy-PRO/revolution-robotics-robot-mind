import unittest

from mock import Mock, patch

from revvy.bluetooth.longmessage import (
    LongMessageHandler,
    LongMessageError,
    LongMessageType,
    LongMessageStatusInfo,
    LongMessageStatus,
    hexdigest2bytes,
    UnusedLongMessageStatusInfo,
)
from revvy.utils.functions import bytestr_hash


class TestLongMessageHandler(unittest.TestCase):

    known_message_types = [
        LongMessageType.FIRMWARE_DATA,
        LongMessageType.FRAMEWORK_DATA,
        LongMessageType.CONFIGURATION_DATA,
        LongMessageType.TEST_KIT,
        LongMessageType.ASSET_DATA,
    ]

    def test_init_is_required_before_write_and_finalize(self):
        handler = LongMessageHandler(None)

        self.assertRaises(LongMessageError, lambda: handler.upload_message([1]))
        self.assertRaises(LongMessageError, handler.finalize_message)

    def test_select_validates_longmessage_type(self):
        handler = LongMessageHandler(None)

        self.assertRaises(LongMessageError, lambda: handler.select_long_message_type(0))
        self.assertRaises(LongMessageError, lambda: handler.select_long_message_type(6))

        for mt in self.known_message_types:
            with self.subTest(mt=mt):
                handler.select_long_message_type(mt)

    def test_reading_not_uploaded_message_returns_unused_status(self):
        storage = Mock()

        storage.read_status = Mock(return_value=UnusedLongMessageStatusInfo)
        storage.set_long_message = Mock()
        storage.get_long_message = Mock()

        handler = LongMessageHandler(storage)

        for mt in self.known_message_types:
            with self.subTest(mt=mt):
                handler.select_long_message_type(mt)
                status = handler.read_status()
                self.assertEqual(LongMessageStatus.UNUSED, status.status)

    def test_reading_previously_uploaded_message_returns_ready_and_metadata(self):
        storage = Mock()

        storage.read_status = Mock(
            return_value=LongMessageStatusInfo(LongMessageStatus.READY, b"md5hash", 123)
        )
        storage.set_long_message = Mock()
        storage.get_long_message = Mock()

        handler = LongMessageHandler(storage)

        for mt in self.known_message_types:
            with self.subTest(mt=mt):
                handler.select_long_message_type(mt)
                status = handler.read_status()
                self.assertEqual(LongMessageStatus.READY, status.status)
                self.assertEqual(b"md5hash", status.md5)
                self.assertEqual(123, status.length)

    def test_reading_during_upload_returns_md5_and_current_length_of_new_message(self):
        storage = Mock()
        new_md5 = bytestr_hash(b"new_md5")
        new_md5_bytes = hexdigest2bytes(new_md5)

        handler = LongMessageHandler(storage)

        for mt in self.known_message_types:
            with self.subTest(mt=mt):
                handler.select_long_message_type(mt)

                handler.init_transfer(new_md5)
                handler.upload_message(b"12345")
                status = handler.read_status()
                self.assertEqual(LongMessageStatus.UPLOAD, status.status)
                self.assertEqual(new_md5_bytes, status.md5)
                self.assertEqual(5, status.length)

                handler.upload_message(b"67890")
                status = handler.read_status()
                self.assertEqual(LongMessageStatus.UPLOAD, status.status)
                self.assertEqual(new_md5_bytes, status.md5)
                self.assertEqual(10, status.length)

    @patch("hashlib.md5", new_callable=Mock)
    def test_finalize_validates_and_stores_uploaded_message(self, mock_hash):
        storage = Mock()
        storage.read_status = Mock(
            return_value=LongMessageStatusInfo(LongMessageStatus.READY, b"new_md5", 123)
        )
        storage.set_long_message = Mock()

        mock_hash.return_value = mock_hash
        mock_hash.update = Mock()
        mock_hash.hexdigest = Mock()

        handler = LongMessageHandler(storage)

        # message invalid
        for mt in self.known_message_types:
            mock_hash.reset_mock()

            mock_hash.hexdigest.return_value = "invalid_md5"
            with self.subTest(mt=f"invalid ({mt})"):
                handler.select_long_message_type(mt)
                handler.init_transfer("new_md5")
                self.assertEqual(1, mock_hash.call_count)

                handler.upload_message(b"12345")
                self.assertEqual(1, mock_hash.update.call_count)
                handler.upload_message(b"67890")
                self.assertEqual(2, mock_hash.update.call_count)

                handler.finalize_message()
                self.assertEqual(1, mock_hash.hexdigest.call_count)

                status = handler.read_status()
                self.assertEqual(LongMessageStatus.VALIDATION_ERROR, status.status)
                self.assertEqual(0, storage.set_long_message.call_count)

        # message valid
        for mt in self.known_message_types:
            mock_hash.reset_mock()
            storage.reset_mock()

            mock_hash.hexdigest.return_value = "new_md5"
            with self.subTest(mt=f"valid ({mt})"):
                handler.select_long_message_type(mt)
                handler.init_transfer("new_md5")
                self.assertEqual(1, mock_hash.call_count)

                handler.upload_message(b"12345")
                self.assertEqual(1, mock_hash.update.call_count)
                handler.upload_message(b"67890")
                self.assertEqual(2, mock_hash.update.call_count)

                handler.finalize_message()
                self.assertEqual(1, mock_hash.hexdigest.call_count)
                self.assertEqual(1, storage.set_long_message.call_count)

                status = handler.read_status()
                self.assertEqual(1, storage.read_status.call_count)
                self.assertEqual(LongMessageStatus.READY, status.status)

    @patch("hashlib.md5", new_callable=Mock)
    def test_finalize_notifies_about_valid_message(self, mock_hash):
        storage = Mock()
        storage.read_status = Mock(
            return_value=LongMessageStatusInfo(LongMessageStatus.READY, b"new_md5", 123)
        )

        mock_hash.return_value = mock_hash
        mock_hash.update = Mock()
        mock_hash.hexdigest = Mock()

        mock_callback = Mock()

        handler = LongMessageHandler(storage)
        handler.on_message_updated.add(mock_callback)

        # message invalid
        for mt in self.known_message_types:
            mock_hash.reset_mock()

            mock_hash.hexdigest.return_value = "invalid_md5"
            with self.subTest(mt=f"invalid ({mt})"):
                handler.select_long_message_type(mt)
                handler.init_transfer("new_md5")
                handler.upload_message(b"12345")
                handler.finalize_message()

                self.assertEqual(0, mock_callback.call_count)

        # message valid
        for mt in self.known_message_types:
            mock_callback.reset_mock()

            mock_hash.hexdigest.return_value = "new_md5"
            with self.subTest(mt=f"valid ({mt})"):
                handler.select_long_message_type(mt)
                handler.init_transfer("new_md5")
                handler.upload_message(b"12345")
                handler.finalize_message()

                self.assertEqual(1, mock_callback.call_count)

    def test_finalize_notifies_for_already_stored_message_without_upload(self):
        info = LongMessageStatusInfo(LongMessageStatus.READY, b"\x01\x23\x45", 123)
        data = b"foobar"

        storage = Mock()
        storage.read_status = Mock(return_value=info)
        storage.set_long_message = Mock()
        storage.get_long_message = Mock(return_value=data)

        mock_callback = Mock()

        handler = LongMessageHandler(storage)
        handler.on_message_updated.add(mock_callback)

        for mt in self.known_message_types:
            mock_callback.reset_mock()
            with self.subTest(mt=mt):
                handler.select_long_message_type(mt)
                handler.finalize_message()
                self.assertTrue(mock_callback.called)
                self.assertEqual(0, storage.set_long_message.call_count)
                self.assertEqual(mt, mock_callback.call_args.args[0].message_type)
                self.assertEqual("012345", mock_callback.call_args.args[0].md5)

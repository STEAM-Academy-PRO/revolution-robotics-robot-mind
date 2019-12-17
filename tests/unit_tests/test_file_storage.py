# SPDX-License-Identifier: GPL-3.0-only

import json
import os
import unittest
from mock.mock import patch, mock_open

from revvy.utils.file_storage import MemoryStorage, StorageElementNotFoundError, IntegrityError, FileStorage


class TestMemoryStorage(unittest.TestCase):
    def test_reading_missing_item_raises_error(self):
        storage = MemoryStorage()

        self.assertRaises(StorageElementNotFoundError, lambda: storage.read_metadata('foo'))
        self.assertRaises(StorageElementNotFoundError, lambda: storage.read('foo'))

    def test_md5_is_stored_if_provided(self):
        storage = MemoryStorage()

        storage.write('foo', b'data')
        self.assertNotEqual('', storage.read_metadata('foo')['md5'])
        self.assertNotEqual(None, storage.read_metadata('foo')['md5'])

    def test_md5_is_calculated_if_not_provided(self):
        storage = MemoryStorage()

        storage.write('foo', b'data', md5='some_md5')
        self.assertEqual('some_md5', storage.read_metadata('foo')['md5'])

    def test_stored_data_can_be_read(self):
        storage = MemoryStorage()

        storage.write('foo', b'data')
        self.assertEqual(b'data', storage.read('foo'))

    def test_stored_data_integrity_is_checked_on_read(self):
        storage = MemoryStorage()

        storage.write('foo', b'data', md5='foobar')
        self.assertRaises(IntegrityError, lambda: storage.read('foo'))


class TestFileStorage(unittest.TestCase):
    @patch('revvy.utils.file_storage.open', new_callable=mock_open)
    def test_folder_access_is_checked_on_init(self, mock):
        FileStorage('.')  # no error raised

        mock.side_effect = IOError
        self.assertRaises(IOError, lambda: FileStorage('.'))

    @patch('revvy.utils.file_storage.read_json')
    @patch('revvy.utils.file_storage.open', new_callable=mock_open)
    def test_read_metadata_raises_if_not_found(self, mock, mock_read):
        storage = FileStorage('.')
        mock_read.side_effect = IOError

        self.assertRaises(StorageElementNotFoundError, lambda: storage.read_metadata('file'))

    @patch('revvy.utils.file_storage.open', new_callable=mock_open)
    def test_read_raises_if_meta_or_data_file_not_found(self, mock):
        storage = FileStorage('.')
        mock.reset_mock()
        mock.side_effect = [IOError, mock.return_value]
        self.assertRaises(StorageElementNotFoundError, lambda: storage.read('file'))

        mock.side_effect = [mock.return_value, IOError]
        self.assertRaises(StorageElementNotFoundError, lambda: storage.read('file'))

    @patch('revvy.utils.file_storage.open', new_callable=mock_open)
    def test_both_metadata_and_data_is_written(self, mock):
        storage = FileStorage('.')
        mock.reset_mock()

        storage.write('file', b'data', md5='md5')

        self.assertEqual(2, mock.call_count)

        called_files = list(map(lambda x: x[0][0], mock.call_args_list))
        expected_files = [
            os.path.join('.', 'file.meta'),
            os.path.join('.', 'file.data')
        ]

        expected_files.sort()
        called_files.sort()

        self.assertListEqual(expected_files, called_files)

    @patch('revvy.utils.file_storage.read_json')
    @patch('revvy.utils.file_storage.open', new_callable=mock_open)
    def test_stored_metadata_can_be_read_back(self, mock, mock_read):
        storage = FileStorage('.')
        mock.reset_mock()

        storage.write('file', b'data', md5='md5')

        # this is fragile since it relies on implementation details
        mock_read.return_value = json.loads("".join(args[0][0] for args in mock().write.call_args_list[1:]))

        meta = storage.read_metadata('file')
        self.assertDictEqual({'md5': 'md5', 'length': 4}, meta)

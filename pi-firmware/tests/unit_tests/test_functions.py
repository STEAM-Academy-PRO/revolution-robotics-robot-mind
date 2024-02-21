import unittest
from mock.mock import Mock, patch, mock_open

from revvy.utils.functions import retry, get_serial


class TestRetry(unittest.TestCase):
    def test_dont_retry_when_successful(self):
        mock = Mock(return_value=True)
        retry(mock, 3)
        self.assertEqual(mock.call_count, 1)

    def test_dont_retry_when_none_is_returned(self):
        mock = Mock(return_value=None)
        retry(mock, 3)
        self.assertEqual(mock.call_count, 1)

    def test_retry_when_exception_is_thrown(self):
        mock = Mock(side_effect=IOError)
        retry(mock, 3)
        self.assertEqual(mock.call_count, 3)

    def test_retry_when_false_is_returned(self):
        mock = Mock(return_value=False)
        retry(mock, 3)
        self.assertEqual(mock.call_count, 3)


class TestGetSerial(unittest.TestCase):
    @patch(
        "revvy.utils.functions.open", new_callable=mock_open, read_data="Serial 1233456789012345"
    )
    def test_valid_cpuid_is_returned(self, mock_file):
        serial = get_serial()
        self.assertEqual(mock_file.call_count, 1)
        self.assertEqual("/proc/cpuinfo", mock_file.call_args[0][0])
        self.assertEqual(serial, "1233456789012345")

    @patch("revvy.utils.functions.open", new_callable=mock_open)
    def test_error_is_returned_if_open_raises(self, mock_file):
        mock_file.side_effect = IOError
        serial = get_serial()
        self.assertEqual(serial, "ERROR000000000")

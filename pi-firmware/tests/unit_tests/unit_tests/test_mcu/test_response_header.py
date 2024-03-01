import unittest

from revvy.mcu.rrrc_transport import ResponseHeader


class TestResponseHeader(unittest.TestCase):
    def test_payload_length_is_unsigned(self):
        header = ResponseHeader.create(b"\x00\xbd\x97\xa1j")

        self.assertTrue(header.payload_length >= 0)

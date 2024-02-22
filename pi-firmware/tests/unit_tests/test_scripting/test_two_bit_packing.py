import unittest

from revvy.utils.bit_packer import pack_2_bit_number_array_32


class TestBitPacker(unittest.TestCase):
    def test_two_bit_conversion_0(self):
        t1 = [0] * 32
        self.assertEqual(pack_2_bit_number_array_32(t1), b"\x00\x00\x00\x00\x00\x00\x00\x00")

    def test_two_bit_conversion_1(self):
        """0101 = 5"""
        t1 = [1] * 32
        self.assertEqual(pack_2_bit_number_array_32(t1), b"\x55\x55\x55\x55\x55\x55\x55\x55")

    def test_two_bit_conversion_2(self):
        """3, 3 => 11 11 => 15 = f"""
        t1 = [3, 3, 3, 3]
        self.assertEqual(pack_2_bit_number_array_32(t1), b"\x00\x00\x00\x00\x00\x00\x00\xff")

    def test_two_bit_conversion_3(self):
        """2, 2, 2, 2 => 10 10 10 10 ... 000 => \\xaa"""
        t1 = [2, 2, 2, 2]
        self.assertEqual(pack_2_bit_number_array_32(t1), b"\x00\x00\x00\x00\x00\x00\x00\xaa")

    def test_two_bit_conversion_4(self):
        """000 ... 0, 0, 0, 1 => (reversed!): 01 00 - 00 00 ... 000  => \\x40"""
        t1 = [0] * 28 + [0, 0, 0, 1]
        self.assertEqual(pack_2_bit_number_array_32(t1), b"\x40\x00\x00\x00\x00\x00\x00\x00")

    def test_two_bit_conversion_5(self):
        """000 ... 0, 0, 0, 2 => (reversed!):  10 00 - 00 00 ... 000 => \\x80"""
        t1 = [0] * 28 + [0, 0, 0, 2]
        self.assertEqual(pack_2_bit_number_array_32(t1), b"\x80\x00\x00\x00\x00\x00\x00\x00")

    def test_two_bit_conversion_6(self):
        """000 ... 2, 0, 0, 0 => (reversed!): 00 00 - 00 10 ... 000  => \\x02"""
        t1 = [0] * 28 + [2, 0, 0, 0]
        self.assertEqual(pack_2_bit_number_array_32(t1), b"\x02\x00\x00\x00\x00\x00\x00\x00")

    def test_two_bit_conversion_7(self):
        """000 ... 3, 3, 0, 0 => (reversed!): 00 00 - 11 11 ... 000  => \\x0f"""
        t1 = [0] * 28 + [3, 3, 0, 0]
        self.assertEqual(pack_2_bit_number_array_32(t1), b"\x0f\x00\x00\x00\x00\x00\x00\x00")

    def test_two_bit_error_more_than_32(self):
        self.assertRaises(ValueError, lambda: pack_2_bit_number_array_32([1] * 33))

    def test_two_bit_error_more_than_3(self):
        self.assertRaises(ValueError, lambda: pack_2_bit_number_array_32([4]))

    def test_two_bit_error_more_than_3_2(self):
        self.assertRaises(ValueError, lambda: pack_2_bit_number_array_32([1241]))

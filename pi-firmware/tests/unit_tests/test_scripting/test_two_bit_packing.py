import unittest

from revvy.utils.bit_packer import pack_2_bit_number_array_32
from revvy.utils.bit_packer import unpack_2_bit_number_array_32


class TestRuntime(unittest.TestCase):
    def test_two_bit_conversion_0(self):
        t1 = [0]*32
        self.assertEqual(pack_2_bit_number_array_32(t1), b'\x00\x00\x00\x00\x00\x00\x00\x00')

    def test_two_bit_conversion_1(self):
        """ 0101 = 5 """
        t1 = [1]*32
        self.assertEqual(pack_2_bit_number_array_32(t1), b'\x55\x55\x55\x55\x55\x55\x55\x55')

    def test_two_bit_conversion_2(self):
        """ 3, 3 => 11 11 => 15 = f """
        t1 = [3, 3, 3, 3]
        self.assertEqual(pack_2_bit_number_array_32(t1), b'\x00\x00\x00\x00\x00\x00\x00\xff')

    def test_two_bit_conversion_3(self):
        """ 2, 2 => 10 10 => \xaa """
        t1 = [2, 2, 2, 2]
        self.assertEqual(pack_2_bit_number_array_32(t1), b'\x00\x00\x00\x00\x00\x00\x00\xaa')

    def test_two_bit_conversion_4(self):
        """ 1, 0, 0, 0 =>  01 00  00 00  => \x40 """
        t1 = [0] * 28 + [1, 0, 0, 0]
        self.assertEqual(pack_2_bit_number_array_32(t1), b'\x00\x00\x00\x00\x00\x00\x00\x01')

    def test_two_bit_conversion_back(self):
        """ 1, 0, 0, 0 =>  01 00  00 00  => \x40 """
        t1 = [0] * 28 + [1, 0, 0, 0]
        self.assertEqual(unpack_2_bit_number_array_32(pack_2_bit_number_array_32(t1)), t1)

    def test_two_bit_conversion_back_1(self):
        t1 = [0] * 28 + [1, 1, 1, 1]
        self.assertEqual(unpack_2_bit_number_array_32(pack_2_bit_number_array_32(t1)), t1)

    def test_two_bit_conversion_back_2(self):
        t1 = [1, 1, 1, 1] * 8
        self.assertEqual(unpack_2_bit_number_array_32(pack_2_bit_number_array_32(t1)), t1)

    def test_two_bit_conversion_back_3(self):
        t1 = [1, 0, 1, 0] * 8
        self.assertEqual(unpack_2_bit_number_array_32(pack_2_bit_number_array_32(t1)), t1)


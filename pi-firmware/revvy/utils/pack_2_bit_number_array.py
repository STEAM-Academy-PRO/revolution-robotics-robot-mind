""" Takes an array of N integers 0..3 and packs them into a struct. """

import struct

def pack_2_bit_number_array(numbers: [int]) -> bytearray:
    """ 11001100... = 3030 """
    packed_value = 0
    for i, num in enumerate(numbers):
        if not 0 <= num < 4:
            raise ValueError("Each number must be a 2-bit number (0, 1, 2, or 3)")
        packed_value |= (num << (2 * i))

    return struct.pack(">Q", packed_value)


def unpack_2_bit_number_array(byte_array: bytearray) -> [int]:
    """ For unpacking """

    result = []
    for byte in byte_array:
        # Extract each 2-bit number from the byte
        for i in range(4):
            two_bit_number = (byte >> (2 * i)) & 0b11
            result.append(two_bit_number)

    return result


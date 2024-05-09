""" Takes an array of N integers 0..3 and packs them into a struct. """

import struct


def pack_2_bit_number_array_32(numbers: list[int]) -> bytearray:
    """
    Returns 8 bytes, filled from the highest index with the 2-bit numbers from the input list.
    converts:  1 2 0 1 => REVERSE: 01 10 00 01 => \x49
    pads the first bytes with zeroes.

    >>> list(pack_2_bit_number_array_32([1, 2, 0, 1]))
    [0, 0, 0, 0, 0, 0, 0, 73]
    """

    packed_value = 0

    if len(numbers) > 32:
        raise ValueError("Only max 32 numbers are allowed.")

    for i, num in enumerate(numbers):
        if not 0 <= num < 4:
            raise ValueError("Each number must be a 2-bit number (0, 1, 2, or 3)")
        packed_value |= num << (2 * i)

    return bytearray(struct.pack(">Q", packed_value))

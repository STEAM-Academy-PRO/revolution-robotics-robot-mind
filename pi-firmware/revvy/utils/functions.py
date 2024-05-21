import hashlib
import json
import traceback
from binascii import b2a_base64, a2b_base64
from typing import Callable, TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from revvy.scripting.variables import Variable

IntOrFloat = TypeVar("IntOrFloat", int, float)


def clip(x: IntOrFloat, min_x: IntOrFloat, max_x: IntOrFloat) -> IntOrFloat:
    """Constrain a number between two limits

    >>> clip(3, 1, 2)
    2
    >>> clip(0, 1, 2)
    1
    >>> clip(1.5, 1, 2)
    1.5
    """
    if x < min_x:
        return min_x
    elif x > max_x:
        return max_x
    else:
        return x


def map_values(x: float, min_x: float, max_x: float, min_y: float, max_y: float) -> float:
    """Scales a number from the input range of [min_x, max_x] to between [min_y, max_y]

    >>> map_values(0.5, 0, 1, 0, 900)
    450.0
    >>> map_values(1.57, 0, 3.14, 0, 180)
    90.0
    >>> map_values(8, 0, 10, 5, 0)
    1.0
    """
    full_scale_in = max_x - min_x
    full_scale_out = max_y - min_y
    return (x - min_x) * (full_scale_out / full_scale_in) + min_y


def get_serial() -> str:
    """Extract serial from cpuinfo file"""

    cpu_serial = "0000000000000000"
    try:
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if line.startswith("Serial"):
                    cpu_serial = line.rstrip()[-16:].lstrip("0")
                    break
    except Exception:
        print("Failed to read cpuid")
        print(traceback.format_exc())
        cpu_serial = "ERROR000000000"

    return cpu_serial


def retry(fn, retries: int = 5, error_handler=None):
    """Retry the given function a number of times, or until it returns True or None"""
    retry_num = 0
    while retry_num < retries:
        try:
            status = fn()
            if status is None:
                return
            elif status:
                return status
        except Exception as e:
            if callable(error_handler):
                error_handler(e)
            else:
                # print(f'repeat threw an error: {str(e)}')
                print(traceback.format_exc())
        retry_num += 1

    return False


def split(data, chunk_size: int):
    """
    >>> list(split([], 5))
    []
    >>> list(split(b'apple', 5))
    [b'apple']
    >>> list(split(b'apple', 7))
    [b'apple']
    >>> list(split([1, 2, 3, 4], 2))
    [[1, 2], [3, 4]]
    >>> list(split([1, 2, 3, 4, 5], 2))
    [[1, 2], [3, 4], [5]]
    >>> list(split(b'apple', 3))
    [b'app', b'le']
    """
    return (data[i : i + chunk_size] for i in range(0, len(data), chunk_size))


def hex2rgb(hex_str: str) -> int:
    """
    >>> '{0:X}'.format(hex2rgb("#aabbcc"))
    'AABBCC'
    >>> hex2rgb("#000000")
    0
    >>> hex2rgb("#0000FF")
    255
    """
    rgb = hex_str.lstrip("#")
    assert len(rgb) == 6, "RGB color must be 6 characters long"
    return int(rgb, 16)


def b64_encode_str(to_encode: str) -> str:
    """
    >>> b64_encode_str("hello")
    'aGVsbG8='
    """
    return b2a_base64(to_encode.encode("utf-8")).decode("utf-8").rstrip()


def b64_decode_str(to_decode: str) -> str:
    """
    >>> b64_decode_str('aGVsbG8=')
    'hello'
    """
    return a2b_base64(to_decode.encode("utf-8")).decode("utf-8")


def is_bit_set(reg, bit) -> bool:
    """
    >>> is_bit_set(1, 0)
    True
    >>> is_bit_set(2, 1)
    True
    >>> is_bit_set(3, 1)
    True
    """
    return reg & (1 << bit) != 0


def bits_to_bool_list(byte_list) -> list[bool]:
    """
    >>> bits_to_bool_list([0xFF])
    [True, True, True, True, True, True, True, True]
    >>> bits_to_bool_list([0x01, 0x00])
    [True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False]
    >>> bits_to_bool_list([0x00, 0x80])
    [False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, True]
    """

    return [is_bit_set(b, bit) for b in byte_list for bit in range(8)]


def bytestr_hash(byte_str: bytes) -> str:
    """
    >>> bytestr_hash(b'hello')
    '5d41402abc4b2a76b9719d911017c592'
    """
    hash_fn = hashlib.md5()
    hash_fn.update(byte_str)
    return hash_fn.hexdigest()


def file_hash(file: str) -> str:
    with open(file, "rb") as f:
        return bytestr_hash(f.read())


def read_json(filename: str):
    with open(filename, "r") as f:
        return json.load(f)


def str_to_func(code: str, script_id=None) -> Callable:
    """Take python code as string and create a callable functions
    The function arguments will be injected into the code as global variables

    >>> code='print(f"Called with {input}")'
    >>> func=str_to_func(code)
    >>> func(input='something')
    Called with something
    """

    def wrapper(**kwargs) -> None:
        kwargs["script_id"] = script_id

        # This list is assembled in `robot_configure`. The mobile app will
        # send a list of variables that we should track.
        # This list is then passed to both background as well as button scripts.
        variable_slots: list["Variable"] = kwargs.get("list_slots", [])

        def ReportVariableChanged(name: str, value):
            # When a variable is changed, update the value in the variable_slots.
            for variable_slot in variable_slots:
                if variable_slot.script == script_id:
                    if variable_slot.name == name:
                        variable_slot.set_value(value)
                        return

        kwargs["ReportVariableChanged"] = ReportVariableChanged

        exec(code, kwargs)

    return wrapper

from enum import Enum

from revvy.mcu.rrrc_control import RevvyControl
from revvy.utils.logger import get_logger


class ErrorType(Enum):
    HardFault = 0
    StackOverflow = 1
    AssertFailure = 2
    TestError = 3
    ImuError = 4
    I2CError = 5


class McuErrorReader:
    def __init__(self, interface: RevvyControl):
        self._log = get_logger('McuErrorReader')
        self._count = interface.error_memory_read_count()
        self._log('Stored errors: ' + self._count)

    @property
    def count(self):
        return self._count

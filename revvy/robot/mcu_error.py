from revvy.mcu.rrrc_control import RevvyControl
from revvy.utils.logger import get_logger


class McuErrorReader:
    def __init__(self, interface: RevvyControl):
        self._log = get_logger('McuErrorReader')
        self._count = interface.error_memory_read_count()
        self._log('Stored errors: ' + self._count)

    @property
    def count(self):
        return self._count


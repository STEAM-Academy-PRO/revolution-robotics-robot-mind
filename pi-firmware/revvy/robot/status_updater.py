from enum import IntEnum
from typing import Callable, Optional
from revvy.mcu.rrrc_control import RevvyControl
from revvy.utils.logger import get_logger


StatusUpdater = Callable[[bytes], None]


class StatusSlot(IntEnum):
    MOTOR_1 = 0
    MOTOR_2 = 1
    MOTOR_3 = 2
    MOTOR_4 = 3
    MOTOR_5 = 4
    MOTOR_6 = 5
    SENSOR_1 = 6
    SENSOR_2 = 7
    SENSOR_3 = 8
    SENSOR_4 = 9
    BATTERY = 10
    ACCELEROMETER = 11
    GYROSCOPE = 12
    RESET = 13
    ORIENTATION = 14

    @staticmethod
    def motor_slot(motor_idx: int) -> "StatusSlot":
        return StatusSlot(StatusSlot.MOTOR_1 + motor_idx)

    @staticmethod
    def sensor_slot(sensor_idx: int) -> "StatusSlot":
        return StatusSlot(StatusSlot.SENSOR_1 + sensor_idx)


class McuStatusUpdater:
    """Class to read status from the MCU.

    This class is the counterpart of the CommWrapper_McuStatusCollector, McuStatusCollector and
    McuStatusSlots components implemented on the MCU. This class is used to enable and read specific
    data slots.

    It was designed to read multiple pieces of data in one run to decrease
    communication interface overhead, thus to allow lower latency updates"""

    def __init__(self, interface: RevvyControl):
        self._interface = interface
        self._is_enabled = [False] * len(StatusSlot)
        self._is_enabled[StatusSlot.RESET.value] = True
        self._handlers: list[Optional[StatusUpdater]] = [None] * len(StatusSlot)
        self._log = get_logger("McuStatusUpdater")

    def reset(self) -> None:
        self._log("reset all slots")
        self._is_enabled = [False] * len(StatusSlot)
        self._is_enabled[StatusSlot.RESET.value] = True
        self._handlers = [None] * len(StatusSlot)
        self._interface.status_updater_reset()

    def enable_slot(self, slot: StatusSlot, callback: StatusUpdater):
        slot_idx = slot.value
        if not self._is_enabled[slot_idx]:
            self._is_enabled[slot_idx] = True
            # self._log(f'enable slot {slot_idx}')
            self._interface.status_updater_control(slot_idx, True)
        self._handlers[slot_idx] = callback

    def disable_slot(self, slot: StatusSlot) -> None:
        slot_idx = slot.value
        if self._is_enabled[slot_idx]:
            self._is_enabled[slot_idx] = False
            self._log(f"disable slot {slot_idx}")
            self._interface.status_updater_control(slot_idx, False)
        self._handlers[slot_idx] = None

    def read(self) -> None:
        data = self._interface.status_updater_read()

        idx = 0
        while idx < len(data):
            data_start = idx + 2
            slot, slot_length = data[idx:data_start]
            idx = data_start + slot_length

            handler = self._handlers[slot]
            if handler:
                handler(data[data_start:idx])

# SPDX-License-Identifier: GPL-3.0-only

from revvy.mcu.rrrc_control import RevvyControl
from revvy.utils.logger import Logger


class McuStatusUpdater:
    mcu_updater_slots = {
        "motor_1": 0,
        "motor_2": 1,
        "motor_3": 2,
        "motor_4": 3,
        "motor_5": 4,
        "motor_6": 5,
        "sensor_1": 6,
        "sensor_2": 7,
        "sensor_3": 8,
        "sensor_4": 9,
        "battery": 10,
        "axl": 11,
        "gyro": 12,
        "yaw": 13,
        "reset": 14
    }
    """Class to read status from the MCU

    This class is the counterpart of McuStatusUpdater/McuStatusUpdaterWrapper implemented on the MCU and is used
    to enable and read specific data slots. It was designed to read multiple pieces of data in one run to decrease
    communication interface overhead, thus to allow lower latency updates"""
    def __init__(self, robot: RevvyControl):
        self._robot = robot
        self._is_enabled = [False] * 32
        self._is_enabled[self.mcu_updater_slots["reset"]] = True
        self._handlers = [lambda x: None] * 32
        self._log = Logger('McuStatusUpdater')

    def reset(self):
        self._log('reset all slots')
        self._handlers = [lambda x: None] * 32
        self._is_enabled = [False] * 32
        self._is_enabled[self.mcu_updater_slots["reset"]] = True
        self._robot.status_updater_reset()

    def _enable_slot(self, slot):
        self._log('enable slot {}'.format(slot))
        self._robot.status_updater_control(slot, True)

    def _disable_slot(self, slot):
        self._log('disable slot {}'.format(slot))
        self._robot.status_updater_control(slot, False)

    def set_slot(self, slot: str, cb):
        slot_idx = self.mcu_updater_slots[slot]
        if callable(cb):
            if not self._is_enabled[slot_idx]:
                self._is_enabled[slot_idx] = True
                self._enable_slot(slot_idx)
            self._handlers[slot_idx] = cb
        else:
            if self._is_enabled[slot_idx]:
                self._is_enabled[slot_idx] = False
                self._disable_slot(slot_idx)
            self._handlers[slot_idx] = lambda x: None

    def read(self):
        data = self._robot.status_updater_read()

        idx = 0
        while idx < len(data):
            slot = data[idx]
            slot_length = data[idx + 1]

            data_start = idx + 2
            data_end = idx + 2 + slot_length

            if data_end <= len(data):
                self._handlers[slot](data[data_start:data_end])
            else:
                self._log('invalid slot length')

            idx = data_end

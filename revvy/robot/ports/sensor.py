# SPDX-License-Identifier: GPL-3.0-only
import struct
from collections import namedtuple

from revvy.functions import map_values
from revvy.mcu.rrrc_control import RevvyControl
from revvy.robot.ports.common import PortHandler, PortInstance


def create_sensor_port_handler(interface: RevvyControl, configs: dict):
    port_amount = interface.get_sensor_port_amount()
    port_types = interface.get_sensor_port_types()

    drivers = {
        'NotConfigured': NullSensor,
        'BumperSwitch': bumper_switch,
        'HC_SR04': hcsr04
    }
    handler = PortHandler(interface, configs, drivers, port_amount, port_types)
    handler._set_port_type = interface.set_sensor_port_type

    return handler


class NullSensor:
    def __init__(self, port: PortInstance, port_config):
        pass

    def on_value_changed(self, cb):
        pass

    def update_status(self, data):
        pass

    @property
    def value(self):
        return 0

    @property
    def raw_value(self):
        return 0


class BaseSensorPortDriver:
    def __init__(self, port: PortInstance):
        self._port = port
        self._interface = port.interface
        self._value = None
        self._raw_value = None
        self._value_changed_callback = lambda p: None

    @property
    def has_data(self):
        return self._value is not None

    def update_status(self, data):
        if len(data) == 0:
            self._value = None
            return

        old_raw = self._raw_value
        if old_raw != data:
            converted = self.convert_sensor_value(data)

            self._raw_value = data
            if converted is not None:
                self._value = converted

            self._raise_value_changed_callback()

    @property
    def value(self):
        return self._value

    @property
    def raw_value(self):
        return self._raw_value

    def on_value_changed(self, cb):
        if not callable(cb):

            def empty_fn(p):
                pass

            cb = empty_fn

        self._value_changed_callback = cb

    def _raise_value_changed_callback(self):
        self._value_changed_callback(self._port)

    def convert_sensor_value(self, raw): raise NotImplementedError


# noinspection PyUnusedLocal
def bumper_switch(port: PortInstance, cfg):
    sensor = BaseSensorPortDriver(port)

    def process_bumper(raw):
        assert len(raw) == 2
        return raw[0] == 1

    sensor.convert_sensor_value = process_bumper
    return sensor


# noinspection PyUnusedLocal
def hcsr04(port: PortInstance, cfg):
    sensor = BaseSensorPortDriver(port)

    def process_ultrasonic(raw):
        assert len(raw) == 4
        dst = int.from_bytes(raw, byteorder='little')
        if dst == 0:
            return None
        return dst

    sensor.convert_sensor_value = process_ultrasonic
    return sensor


class Ev3Mode:
    _type_info = [
        {'data_size': 1, 'read_pattern': 'B'},
        {'data_size': 1, 'read_pattern': 'b'},
        {'data_size': 2, 'read_pattern': '<H'},
        {'data_size': 2, 'read_pattern': '<h'},
        {'data_size': 2, 'read_pattern': '>h'},
        {'data_size': 4, 'read_pattern': '<l'},
        {'data_size': 4, 'read_pattern': '>l'},
        {'data_size': 4, 'read_pattern': '<f'}
    ]

    def __init__(self, n_samples, data_type, figures, decimals, raw_min, raw_max, pct_min, pct_max, si_min, si_max):
        self._nSamples = n_samples
        self._dataType = data_type
        self._figures = figures
        self._decimals = decimals
        self._raw_min = raw_min
        self._raw_max = raw_max
        self._pct_min = pct_min
        self._pct_max = pct_max
        self._si_min = si_min
        self._si_max = si_max

    def _convert_single(self, value):
        return map_values(value, self._raw_min, self._raw_max, self._si_min, self._si_max)

    def convert(self, data):
        data_size = self._type_info[self._dataType]['data_size']

        start = 0
        values = []
        for i in range(0, self._nSamples):
            value = struct.unpack(self._type_info[self._dataType]['read_pattern'], data[start:start+data_size])
            start += data_size

            values.append(self._convert_single(value))

        return values


class Ev3UARTSensor(BaseSensorPortDriver):
    STATE_RESET = 0
    STATE_CONFIGURE = 1
    STATE_DATA = 2

    MODE_MASK = 0x07
    REMOTE_STATUS_MASK = 0xC0
    REMOTE_STATES = {
        0x00: STATE_RESET,
        0x40: STATE_CONFIGURE,
        0x80: STATE_DATA
    }

    def __init__(self, port: PortInstance, modes=None):
        super().__init__(port)
        self._state = self.STATE_RESET
        self._modes = modes
        self._current_mode = 0

    def select_mode(self, mode):
        if mode < len(self._modes):
            self._interface.set_sensor_port_config(self._port.id, [mode])
            self._current_mode = mode

    def convert_sensor_value(self, raw):
        if len(raw) == 0:
            return None

        try:
            state = self.REMOTE_STATES[raw[0] & self.REMOTE_STATUS_MASK]

            if self._state != state:
                if state == self.STATE_DATA:
                    if self._modes is None:
                        self._modes = self._get_modes()
                    self.on_configured()
                self._state = state

            if state == self.STATE_DATA:

                mode_idx = raw[0] & self.MODE_MASK
                if mode_idx == self._current_mode:
                    try:
                        mode = self._modes[mode_idx]

                        return mode.convert(raw)
                    except IndexError:
                        return None
                else:
                    # handle case when mode switch does not happen (count wrong messages, reconfigure/reset)
                    pass

        except KeyError:
            return None

    def _get_modes(self):
        sensor_info = self._interface.read_sensor_info(self._port.id, 0)

        (sensor_type, speed, nModes, nViews) = struct.unpack('<blbb', sensor_info)

        modes = []
        for i in range(0, nModes):
            mode_info = self._interface.read_sensor_info(self._port.id, i + 1)
            (nSamples, dataType, figures, decimals,
             raw_min, raw_max,
             pct_min, pct_max,
             si_min, si_max) = struct.unpack('<' + 'b'*4 + 'f'*6, mode_info)

            modes.append(Ev3Mode(nSamples, dataType, figures, decimals,
                                 raw_min, raw_max,
                                 pct_min, pct_max,
                                 si_min, si_max))

        return modes

    def on_configured(self):
        pass

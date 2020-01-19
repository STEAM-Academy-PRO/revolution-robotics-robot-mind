# SPDX-License-Identifier: GPL-3.0-only
import collections
import struct
from functools import partial

from revvy.utils.functions import map_values, split
from revvy.mcu.rrrc_control import RevvyControl
from revvy.robot.ports.common import PortHandler, PortInstance, PortDriver


def create_sensor_port_handler(interface: RevvyControl):
    port_amount = interface.get_sensor_port_amount()
    port_types = interface.get_sensor_port_types()

    drivers = {
        'BumperSwitch': bumper_switch,
        'HC_SR04': hcsr04,
        'EV3': lambda port, cfg: Ev3UARTSensor(port),
        'EV3_Color': ev3_color
    }
    handler = PortHandler("Sensor", interface, drivers, NullSensor(), port_amount, port_types)
    handler._set_port_type = interface.set_sensor_port_type

    return handler


class NullSensor(PortDriver):
    def __init__(self):
        super().__init__('NotConfigured')

    def on_port_type_set(self):
        pass

    def update_status(self, data):
        pass

    @property
    def value(self):
        return 0

    @property
    def raw_value(self):
        return 0


class BaseSensorPortDriver(PortDriver):
    def __init__(self, driver, port: PortInstance):
        super().__init__(driver)
        self._port = port
        self._interface = port.interface
        self._value = None
        self._raw_value = None
        self._value_changed_callback = None

    def on_port_type_set(self):
        pass

    @property
    def has_data(self):
        return self._value is not None

    def update_status(self, data):
        if len(data) == 0:
            self._value = None
            return

        if self._raw_value == data:
            return

        self._raw_value = data
        converted = self.convert_sensor_value(data)

        self._raw_value = data
        if converted is not None:
            self._value = converted

        self.on_status_changed(self._port)

    @property
    def value(self):
        return self._value

    @property
    def raw_value(self):
        return self._raw_value

    def convert_sensor_value(self, raw): raise NotImplementedError


# noinspection PyUnusedLocal
def bumper_switch(port: PortInstance, cfg):
    sensor = BaseSensorPortDriver('BumperSwitch', port)

    def process_bumper(raw):
        assert len(raw) == 2
        return raw[0] == 1

    sensor.convert_sensor_value = process_bumper
    return sensor


# noinspection PyUnusedLocal
def hcsr04(port: PortInstance, cfg):
    sensor = BaseSensorPortDriver('HC_SR04', port)

    def process_ultrasonic(raw):
        assert len(raw) == 4
        (dst, ) = struct.unpack("<l", raw)
        if dst == 0:
            return None
        return dst

    sensor.convert_sensor_value = process_ultrasonic
    return sensor


Ev3DataType = collections.namedtuple("Ev3DataType", ['data_size', 'read_pattern', 'name'])


class Ev3Mode:
    mode_info_pattern = '<' + 'b' * 4 + 'f' * 6

    @staticmethod
    def parse(mode_info):
        (nSamples, dataType, figures, decimals,
         raw_min, raw_max,
         pct_min, pct_max,
         si_min, si_max) = struct.unpack(Ev3Mode.mode_info_pattern, mode_info)

        return Ev3Mode(nSamples, dataType, figures, decimals, raw_min, raw_max, pct_min, pct_max, si_min,
                       si_max)

    _type_info = [
        Ev3DataType(data_size=1, read_pattern='B', name='u8'),
        Ev3DataType(data_size=1, read_pattern='b', name='s8'),
        Ev3DataType(data_size=2, read_pattern='<H', name='u16'),
        Ev3DataType(data_size=2, read_pattern='<h', name='s16'),
        Ev3DataType(data_size=2, read_pattern='>h', name='s16be'),
        Ev3DataType(data_size=4, read_pattern='<l', name='s32'),
        Ev3DataType(data_size=4, read_pattern='>l', name='s32be'),
        Ev3DataType(data_size=4, read_pattern='<f', name='float')
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

        print('Datasets: {}'.format(self._nSamples))
        print('DataType: {}'.format(self._type_info[self._dataType].name))
        print('Format: {}.{}'.format(self._figures, self._decimals))
        print('Raw: {}-{}'.format(self._raw_min, self._raw_max))
        print('%: {}-{}'.format(self._pct_min, self._pct_max))
        print('SI: {}-{}'.format(self._si_min, self._si_max))

    def _convert_single(self, value):
        return map_values(value, self._raw_min, self._raw_max, self._si_min, self._si_max)

    def convert(self, data):
        type_info = self._type_info[self._dataType]

        values = []
        for chunk in split(data, type_info.data_size):
            (value,) = struct.unpack(type_info.read_pattern, chunk)

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
        super().__init__('EV3', port)
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

                        return mode.convert(raw[1:])
                    except IndexError:
                        return None
                else:
                    # handle case when mode switch does not happen (count wrong messages, reconfigure/reset)
                    pass

        except KeyError:
            return None

    def _get_modes(self):
        sensor_info = self._interface.read_sensor_info(self._port.id, 0)

        if sensor_info:
            (sensor_type, speed, nModes, nViews) = struct.unpack('<blbb', sensor_info)

            modes = []
            for i in range(1, nModes+1):
                mode_info = self._interface.read_sensor_info(self._port.id, i)
                print('New mode: {}/{}'.format(i, nModes))
                print('===============')
                modes.append(Ev3Mode.parse(mode_info))
                print('')

            return modes

    def on_configured(self):
        pass


class Color:
    def __init__(self, color_id, name, rgb):
        self._id = color_id
        self._name = name
        self._rgb = rgb

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name

    @property
    def rgb(self):
        return self._rgb

    def __str__(self) -> str:
        return self._name


def ev3_color(port: PortInstance, cfg):
    sensor = Ev3UARTSensor(port)

    color_map = [
        {'name': 'No color', 'rgb': '#000000'},
        {'name': 'Black',    'rgb': '#000000'},
        {'name': 'Blue',     'rgb': '#0000ff'},
        {'name': 'Green',    'rgb': '#00ff00'},
        {'name': 'Yellow',   'rgb': '#00ffff'},
        {'name': 'Red',      'rgb': '#ff0000'},
        {'name': 'White',    'rgb': '#ffffff'},
        {'name': 'Brown',    'rgb': '#ffff00'}
    ]

    # we'll replace the general convert_sensor_value method with a specialized one so copy the old one
    ev3_convert = sensor.convert_sensor_value

    def convert(raw):
        value = ev3_convert(raw)
        if value:
            color_id = int(value[0])
            color_data = color_map[color_id]
            return Color(color_id=color_id, name=color_data['name'], rgb=color_data['rgb'])

    sensor.convert_sensor_value = convert
    sensor.on_configured = partial(sensor.select_mode, 2)

    return sensor

# SPDX-License-Identifier: GPL-3.0-only

import json
from json import JSONDecodeError

from revvy.robot.configurations import Motors, Sensors
from revvy.scripting.runtime import ScriptDescriptor
from revvy.utils.functions import b64_decode_str, dict_get_first, str_to_func
from revvy.scripting.builtin_scripts import builtin_scripts
from revvy.utils.logger import get_logger

_log = get_logger('RobotConfig')

motor_types = [
    None,
    Motors.RevvyMotor,
    # motor
    [
        [  # left
            Motors.RevvyMotor_CCW,
            Motors.RevvyMotor
        ],
        [  # right
            Motors.RevvyMotor,
            Motors.RevvyMotor_CCW
        ]
    ]
]

motor_sides = ["left", "right"]

sensor_types = [
    None,
    Sensors.Ultrasonic,
    Sensors.BumperSwitch,
    Sensors.EV3_Color,
    Sensors.SofteqCS,
]


class PortConfig:
    def __init__(self):
        self._ports = {}
        self._port_names = {}

    @property
    def names(self):
        return self._port_names

    def __getitem__(self, item):
        return self._ports.get(item)

    def __setitem__(self, item, value):
        self._ports[item] = value


class RemoteControlConfig:
    def __init__(self):
        self.analog = []
        self.buttons = {}
        self.variable_slots = []


class ConfigError(Exception):
    pass


def dict_get_by_keys(s, keys):
    for k in keys:
        if k in s:
            return s[k]
    return None


def get_runnable_from_script(s, script_idx):
    builtin_script_name = dict_get_by_keys(s,
        ['builtinScriptName', 'builtinscriptname'])
    result = builtin_scripts.setdefault(builtin_script_name, None)
    if result:
        _log(f'Use builtin script: {builtin_script_name}')
        return result

    embedded_script = dict_get_by_keys(s,
        ['pythonCode', 'pythoncode'])

    if not embedded_script:
        _log('\'builtinScriptName\' or \'pythonCode\' not found in script')
        return None

    python_code = b64_decode_str(embedded_script)
    _log(f'Use python code as script: {python_code}')

    python_code = python_code.replace('import time\n', '')
    return str_to_func(python_code, script_idx)


def make_script_name_common(script_idx, assignment_type, detail):
    return 'script_{}_{}_{}'.format(
        script_idx, assignment_type, detail)


def make_analog_script_name(a, script_idx):
    detail = 'channels_' + '_'.join(map(str, a['channels']))
    return make_script_name_common(script_idx, 'analog', detail)


def make_button_script_name(script_idx, button_idx):
    return make_script_name_common(script_idx,
        'button', f'{button_idx}')


def robot_config_process_script(config, script, script_idx):
    _log(f'Processing script #{script_idx}')
    runnable = get_runnable_from_script(script, script_idx)
    if not runnable:
        raise KeyError(f'No code in script {script}')

    assignments = script.setdefault('assignments', None)
    if not assignments:
        raise KeyError(f'No assignments in script {script}')


    for a in assignments.setdefault('analog', []):
        script_name = make_analog_script_name(a, script_idx)
        priority = a['priority']
        script_desc = ScriptDescriptor(script_name, runnable, priority)
        config.controller.analog.append({
            'channels': a['channels'],
            'script': script_desc
        })

    for v in assignments.setdefault('variableSlots', []):
        config.controller.variable_slots.append({
            'slot': v['slot'],
            'name': v['variable'],
            'script': script_idx,
        })

    for b in assignments.setdefault('buttons', []):
        button_idx = b['id']
        script_name = make_button_script_name(script_idx, button_idx)
        priority = b['priority']
        script_desc = ScriptDescriptor(script_name, runnable, priority)
        config.controller.buttons[button_idx] = script_desc

    if 'background' in assignments:
        script_name = make_script_name_common(script_idx, "backgroud", "0")
        priority = assignments['background']
        script_desc = ScriptDescriptor(script_name, runnable, priority)
        config.background_scripts.append(script_desc)


class RobotConfig:
    @staticmethod
    def from_string(config_string):
        try:
            json_config = json.loads(config_string)
        except JSONDecodeError as e:
            raise ConfigError('Received configuration is not a valid json string') from e

        config = RobotConfig()
        robot_config_keys = ['robotConfig', 'robotconfig']
        robot_config = dict_get_by_keys(json_config, robot_config_keys)
        if robot_config is None:
            raise ConfigError(f'Config missing any of these keys: {robot_config_keys}')

        blockly_list_keys = ['blocklyList', 'blocklylist']
        blockly_list = dict_get_by_keys(json_config, blockly_list_keys)
        if blockly_list is None:
            raise ConfigError(f'Config missing any of these keys: {blockly_list_keys}')

        initial_state = dict_get_by_keys(json_config,
            ['initialState', 'initialstate'])
        if initial_state:
            config.background_initial_state = initial_state

        try:
            for script_idx, script in enumerate(blockly_list):
                 robot_config_process_script(config, script, script_idx)
        except (TypeError, IndexError, KeyError, ValueError) as e:
            raise ConfigError('Failed to decode received controller configuration') from e

        try:
            i = 1
            motors = robot_config.get('motors', []) if type(robot_config) is dict else []
            for motor in motors:
                if not motor:
                    motor = {'type': 0}

                if motor['type'] == 2:
                    # drivetrain
                    motor_type = motor_types[2][motor['side']][motor['reversed']]
                    config.drivetrain[motor_sides[motor['side']]].append(i)

                else:
                    motor_type = motor_types[motor['type']]

                if motor_type is not None:
                    config.motors.names[motor['name']] = i

                config.motors[i] = motor_type
                i += 1
        except (TypeError, IndexError, KeyError, ValueError) as e:
            raise ConfigError('Failed to decode received motor configuration') from e

        try:
            i = 1
            sensors = robot_config.get('sensors', []) if type(robot_config) is dict else []
            print(sensors)
            for sensor in sensors:
                if not sensor:
                    sensor = {'type': 0}

                sensor_type = sensor_types[sensor['type']]

                if sensor_type is not None:
                    config.sensors.names[sensor['name']] = i

                config.sensors[i] = sensor_type
                i += 1

        except (TypeError, IndexError, KeyError, ValueError) as e:
            raise ConfigError('Failed to decode received sensor configuration') from e

        return config

    def __init__(self):
        self.motors = PortConfig()
        self.sensors = PortConfig()
        self.drivetrain = {'left': [], 'right': []}
        self.controller = RemoteControlConfig()
        self.background_scripts = []
        self.background_initial_state = 'running'


empty_robot_config = RobotConfig()

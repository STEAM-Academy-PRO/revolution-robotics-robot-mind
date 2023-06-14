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
        self.buttons = [None] * 32
        self.variable_slots = []


class ConfigError(Exception):
    pass


def dict_get_by_keys(s, keys):
    for k in keys:
        if k in s:
            return s[k]
    return None


def get_runnable_from_script(s, script_id):
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
    return str_to_func(python_code, script_id)


class RobotConfig:
    @staticmethod
    def from_string(config_string):
        try:
            json_config = json.loads(config_string)
        except JSONDecodeError as e:
            raise ConfigError('Received configuration is not a valid json string') from e

        config = RobotConfig()
        try:
            robot_config = dict_get_first(json_config, ['robotConfig', 'robotconfig'])
            blockly_list = dict_get_first(json_config, ['blocklyList', 'blocklylist'])
        except KeyError as e:
            raise ConfigError('Received configuration is missing required parts') from e

        try:
            config.background_initial_state = dict_get_first(json_config, ['initialState', 'initialstate'])
        except KeyError:
            pass

        try:
            i = 0
            for script in blockly_list:
                _log(f'Processing script #{i}')
                runnable = get_runnable_from_script(script, i)
                if not runnable:
                    raise KeyError(f'No code in script {script}')

                assignments = script['assignments']
                # script names are mostly relevant for logging
                for analog_assignment in assignments.setdefault('analog', []):
                    channels = ', '.join(map(str, analog_assignment['channels']))
                    script_name = f'[script {i}] analog channels {channels}'
                    priority = analog_assignment['priority']
                    config.controller.analog.append(
                            {
                        'channels': analog_assignment['channels'],
                        'script': ScriptDescriptor(script_name, runnable, priority)})
                    i += 1

                for variable_assignments in assignments.setdefault('variableSlots', []):
                    variable_slot = variable_assignments['slot']
                    variable_name = variable_assignments['variable']
                    config.controller.variable_slots.append({'slot': variable_slot,
                                                             'variable': variable_name,
                                                             'script': i,
                                                             })

                for button_assignment in assignments.setdefault('buttons', []):
                    button_id = button_assignment['id']
                    script_name = f'[script {i}] button {button_id}'
                    priority = button_assignment['priority']
                    config.controller.buttons[button_id] = ScriptDescriptor(script_name, runnable, priority)
                    i += 1

                if 'background' in assignments:
                    script_name = f'[script {i}] background'
                    priority = assignments['background']
                    config.background_scripts.append(ScriptDescriptor(script_name, runnable, priority))
                    i += 1
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

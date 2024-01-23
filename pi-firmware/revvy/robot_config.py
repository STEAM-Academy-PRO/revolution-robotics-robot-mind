
import json
from json import JSONDecodeError

from revvy.robot.configurations import Motors, Sensors
from revvy.scripting.runtime import ScriptDescriptor
from revvy.utils.functions import b64_decode_str, str_to_func
from revvy.scripting.builtin_scripts import builtin_scripts
from revvy.utils.logger import get_logger

log = get_logger('RobotConfig')

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


def make_script_name_common(script_idx, assignment_type, detail):
    return 'script_{}_{}_{}'.format(
        script_idx, assignment_type, detail)


def make_analog_script_name(analog, script_idx):
    detail = 'channels_' + '_'.join(map(str, analog['channels']))
    return make_script_name_common(script_idx, 'analog', detail)


def make_button_script_name(script_idx, button_idx):
    return make_script_name_common(script_idx,
        'button', f'{button_idx}')


def json_get_field(obj, keys, optional, value_type=None):
    is_found = False
    value = None

    for key in keys:
        if key in obj:
            is_found = True
            value = obj[key]
            break

    if not is_found:
        if optional:
            return None

        raise ConfigError(
            'Mandatory config field missing: key(s):{}, type:{}'.format(
                keys, value_type))

    # value_type omitted, check not required
    if value_type is None:
        return value

    if isinstance(value, value_type):
        return value

    raise ConfigError(
        'Wrong config field type: key(s):{}, type:{}, required:{}'.format(
            keys, type(value), value_type))


class RobotConfig:
    @staticmethod
    def create_runnable(script, script_num):
        script_name = json_get_field(script,
            ['builtinScriptName', 'builtinscriptname'], optional=True)

        if script_name:
            if script_name not in builtin_scripts:
                raise KeyError(f'Builtin script "{script_name}" does not exist')

            log(f'Use builtin script: {script_name}')
            return builtin_scripts[script_name]

        source_b64 = json_get_field(script, ['pythonCode', 'pythoncode'],
            optional=True)

        if not source_b64:
            raise KeyError('Neither builtinScriptName, nor pythonCode is present for a script')

        code = b64_decode_str(source_b64)
        log('Use python code as script')

        code = code.replace('import time\n', '')
        return str_to_func(code, script_num)

    @staticmethod
    def process_script(config, script, script_idx):
        log(f'Processing script #{script_idx}')
        runnable = RobotConfig.create_runnable(script, script_idx)

        assignments = script['assignments']
        # script names are mostly relevant for logging
        for analog_assignment in assignments.setdefault('analog', []):
            script_name = make_analog_script_name(analog_assignment, script_idx)
            priority = analog_assignment['priority']
            script_desc = ScriptDescriptor(script_name, runnable, priority)
            config.controller.analog.append({
                'channels': analog_assignment['channels'],
                'script': script_desc
            })

        for variable_assignments in assignments.setdefault('variableSlots', []):
            config.controller.variable_slots.append({
                'slot': variable_assignments['slot'],
                'variable': variable_assignments['variable'],
                'script': script_idx
            })

        for button_assignment in assignments.setdefault('buttons', []):
            button_idx = button_assignment['id']
            script_name = make_button_script_name(script_idx, button_idx)
            priority = button_assignment['priority']
            script_desc = ScriptDescriptor(script_name, runnable, priority)
            config.controller.buttons[button_idx] = script_desc

        if 'background' in assignments:
            script_name = make_script_name_common(script_idx, "background", "0")
            priority = assignments['background']
            script_desc = ScriptDescriptor(script_name, runnable, priority)
            config.background_scripts.append(script_desc)

    @staticmethod
    def from_string(config_string):
        try:
            json_config = json.loads(config_string)
        except JSONDecodeError as e:
            raise ConfigError('Received configuration is not a valid json string') from e

        log("\n"+json.dumps(json_config, indent=2))

        config = RobotConfig()
        robot_config = json_get_field(json_config,
            ['robotConfig', 'robotconfig'], optional=False, value_type=dict)

        blockly_list = json_get_field(json_config,
            ['blocklyList', 'blocklylist'], optional=True, value_type=list)

        initial_state = json_get_field(json_config,
            ['initialState', 'initialstate'], optional=True, value_type=str)

        if initial_state:
            config.background_initial_state = initial_state
        else:
            # If 'initialState' is not set, default is 'running' which will start all
            # background scripts at the start of play session.
            config.background_initial_state = 'running'

        try:
            for script_idx, script in enumerate(blockly_list):
                RobotConfig.process_script(config, script, script_idx)
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
        self.background_initial_state = None


empty_robot_config = RobotConfig()

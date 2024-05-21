import json
from json import JSONDecodeError
from typing import Optional, TypeVar

from revvy.robot.configurations import Motors, Sensors, ccw_motor
from revvy.robot.ports.common import DriverConfig
from revvy.scripting.runtime import ScriptDescriptor
from revvy.utils.functions import b64_decode_str, str_to_func
from revvy.scripting.builtin_scripts import builtin_scripts
from revvy.utils.logger import get_logger

log = get_logger("RobotConfig")


class PortConfig:
    """Configuration data for a set of ports, indexed by port id."""

    def __init__(self, capacity: int) -> None:
        self._ports: list[Optional[DriverConfig]] = [None] * capacity  # id -> port config
        self._port_names: dict[str, int] = {}  # name -> id
        self._configured = 0

    @property
    def names(self) -> dict[str, int]:
        return self._port_names

    def __getitem__(self, item: int) -> Optional[DriverConfig]:
        """Returns a DriverConfig or None if the port is not configured"""
        try:
            return self._ports[item]
        except IndexError as e:
            raise IndexError(f"Port index out of range: {item}") from e

    def len(self) -> int:
        return self._configured

    def add(self, item: Optional[DriverConfig], alias: str):
        if len(self._ports) == self._configured:
            raise IndexError(f"Can not add more than {len(self._ports)} ports")

        id = self._configured

        if item is not None:
            if alias in self.names:
                raise KeyError(f"Port name already exists: {alias}")
            self.names[alias] = id
            self._ports[id] = item

        self._configured += 1


class RemoteControlConfig:
    def __init__(self) -> None:
        self.analog = []
        self.buttons: list[Optional[ScriptDescriptor]] = [None] * 32
        self.variable_slots = []


class ConfigError(Exception):
    pass


def make_script_name_common(script_idx, assignment_type, detail) -> str:
    return f"script_{script_idx}_{assignment_type}_{detail}"


def make_analog_script_name(analog, script_idx) -> str:
    detail = "channels_" + "_".join(map(str, analog["channels"]))
    return make_script_name_common(script_idx, "analog", detail)


def make_button_script_name(script_idx, button_idx) -> str:
    return make_script_name_common(script_idx, "button", f"{button_idx}")


JsonValue = TypeVar("JsonValue")


def json_get_field(obj, keys, value_type: type[JsonValue]) -> JsonValue:
    is_found = False
    value = None

    for key in keys:
        if key in obj:
            is_found = True
            value = obj[key]
            break

    if not is_found:
        raise ConfigError(
            "Mandatory config field missing: key(s):{}, type:{}".format(keys, value_type)
        )

    if isinstance(value, value_type):
        return value

    raise ConfigError(
        "Wrong config field type: key(s):{}, type:{}, required:{}".format(
            keys, type(value), value_type
        )
    )


def json_get_field_optional(obj, keys, value_type: type[JsonValue]) -> Optional[JsonValue]:
    is_found = False
    value = None

    for key in keys:
        if key in obj:
            is_found = True
            value = obj[key]
            break

    if not is_found:
        return None

    # value_type omitted, check not required
    if value_type is None:
        return value

    if isinstance(value, value_type):
        return value

    raise ConfigError(
        "Wrong config field type: key(s):{}, type:{}, required:{}".format(
            keys, type(value), value_type
        )
    )


class DrivetrainConfig:
    def __init__(self) -> None:
        self.left = []
        self.right = []

    def add(self, side: int, motor: int):
        if side == 0:
            self.left.append(motor)
        else:
            self.right.append(motor)


class RobotConfig:
    @staticmethod
    def create_runnable(script: dict, script_num: int):
        script_name = json_get_field_optional(
            script, ["builtinScriptName", "builtinscriptname"], value_type=str
        )

        if script_name:
            if script_name not in builtin_scripts:
                raise KeyError(f'Builtin script "{script_name}" does not exist')

            log(f"Use builtin script: {script_name}")
            return builtin_scripts[script_name], f"built in script: {script_name}"

        source_b64 = json_get_field_optional(script, ["pythonCode", "pythoncode"], value_type=str)

        if not source_b64:
            raise KeyError("Neither builtinScriptName, nor pythonCode is present for a script")

        script_source_code = b64_decode_str(source_b64)
        log("Use python code as script")

        ### TODO: This is a HACK!!! Blockly should not be generating
        # import time\n headers, if we do not want them.
        # We re-bind time.sleep to refer to the thread context's function, so we can interrupt it
        script_source_code = script_source_code.replace("import time\n", "")

        return str_to_func(script_source_code, script_num), script_source_code

    def process_script(self, script: dict, script_idx: int):
        log(f"Processing script #{script_idx}")
        runnable, source = RobotConfig.create_runnable(script, script_idx)

        assignments: dict = script["assignments"]
        # script names are mostly relevant for logging
        for analog_assignment in assignments.setdefault("analog", []):
            script_name = make_analog_script_name(analog_assignment, script_idx)
            priority = analog_assignment["priority"]
            script_desc = ScriptDescriptor(script_name, runnable, priority, source=source)
            self.controller.analog.append(
                {"channels": analog_assignment["channels"], "script": script_desc}
            )

        for variable_assignments in assignments.setdefault("variableSlots", []):
            self.controller.variable_slots.append(
                {
                    "slot": variable_assignments["slot"],
                    "variable": variable_assignments["variable"],
                    "script": script_idx,
                }
            )

        for button_assignment in assignments.setdefault("buttons", []):
            button_idx = button_assignment["id"]
            script_name = make_button_script_name(script_idx, button_idx)
            priority = button_assignment["priority"]
            script_desc = ScriptDescriptor(
                script_name, runnable, priority, source=source, ref_id=button_idx
            )
            self.controller.buttons[button_idx] = script_desc

        if "background" in assignments:
            script_name = make_script_name_common(script_idx, "background", "0")
            priority = assignments["background"]
            script_desc = ScriptDescriptor(
                script_name, runnable, priority, source=source, ref_id=script_idx
            )
            self.background_scripts.append(script_desc)

    def add_motor(self, config: Optional[DriverConfig], alias: str):
        self.motors.add(config, alias)

    def add_sensor(self, config: Optional[DriverConfig], alias: str):
        self.sensors.add(config, alias)

    def add_motor_from_json(self, motor: Optional[dict]):
        i = self.motors.len()
        if not motor:
            motor = {"type": 0}

        MOTOR_TYPES = [
            None,
            Motors.RevvyMotor,
            # motor
            [
                [ccw_motor(Motors.RevvyMotor), Motors.RevvyMotor],  # left
                [Motors.RevvyMotor, ccw_motor(Motors.RevvyMotor)],  # right
            ],
        ]

        if motor["type"] == 2:
            # drivetrain
            motor_type = MOTOR_TYPES[2][motor["side"]][motor["reversed"]]

            # register drivetrain motors automatically
            self.drivetrain.add(motor["side"], i)
        else:
            motor_type = MOTOR_TYPES[motor["type"]]

        self.add_motor(motor_type, motor.get("name", f"motor{i+1}"))

    def add_sensor_from_json(self, sensor: Optional[dict]):
        i = self.sensors.len()

        if not sensor:
            sensor = {"type": 0, "name": f"sensor{i+1}"}

        SENSOR_TYPES = [
            None,
            Sensors.Ultrasonic,
            Sensors.BumperSwitch,
            None,
            Sensors.SofteqCS,
        ]

        self.add_sensor(SENSOR_TYPES[sensor["type"]], sensor.get("name", f"motor{i+1}"))

    @staticmethod
    def from_string(config_string: str) -> "RobotConfig":
        try:
            json_config = json.loads(config_string)
        except JSONDecodeError as e:
            raise ConfigError("Received configuration is not a valid json string") from e

        log("\n" + json.dumps(json_config, indent=2))

        config = RobotConfig()
        robot_config = json_get_field(json_config, ["robotConfig", "robotconfig"], value_type=dict)

        blockly_list = json_get_field_optional(
            json_config, ["blocklyList", "blocklylist"], value_type=list
        )

        initial_state = json_get_field_optional(
            json_config, ["initialState", "initialstate"], value_type=str
        )

        if initial_state:
            config.background_initial_state = initial_state
        else:
            # If 'initialState' is not set, default is 'running' which will start all
            # background scripts at the start of play session.
            config.background_initial_state = "running"

        if blockly_list is not None:
            try:
                for script_idx, script in enumerate(blockly_list):
                    config.process_script(script, script_idx)
            except (TypeError, IndexError, KeyError, ValueError) as e:
                raise ConfigError("Failed to decode received controller configuration") from e

        try:
            for motor in robot_config.get("motors", []):
                config.add_motor_from_json(motor)
        except (TypeError, IndexError, KeyError, ValueError) as e:
            raise ConfigError("Failed to decode received motor configuration") from e

        try:
            for sensor in robot_config.get("sensors", []):
                config.add_sensor_from_json(sensor)
        except (TypeError, IndexError, KeyError, ValueError) as e:
            raise ConfigError("Failed to decode received sensor configuration") from e

        return config

    def __init__(self) -> None:
        self.motors = PortConfig(6)
        self.sensors = PortConfig(4)
        self.drivetrain = DrivetrainConfig()
        self.controller = RemoteControlConfig()
        self.background_scripts = []
        self.background_initial_state = None


empty_robot_config = RobotConfig()

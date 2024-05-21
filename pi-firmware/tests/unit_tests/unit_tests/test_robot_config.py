import unittest

from revvy.robot.configurations import Sensors, Motors, ccw_motor
from revvy.scripting.builtin_scripts import drive_2sticks
from revvy.utils.functions import b64_encode_str
from revvy.robot_config import RobotConfig, ConfigError


class TestRobotConfig(unittest.TestCase):
    def test_not_valid_config_is_ignored(self):
        self.assertRaises(ConfigError, lambda: RobotConfig.from_string("not valid json"))

    def test_valid_config_needs_robotConfig_and_blocklies_keys(self):
        with self.subTest("Blockly only"):
            self.assertRaises(ConfigError, lambda: RobotConfig.from_string('{"blocklies": []}'))

        with self.subTest("Robot Config only"):
            self.assertRaises(ConfigError, lambda: RobotConfig.from_string('{"robotConfig": []}'))

        # these should not raise ConfigError
        with self.subTest("Both"):
            RobotConfig.from_string('{"robotConfig": {}, "blocklyList": []}')

        with self.subTest("Both, lowercase"):
            RobotConfig.from_string('{"robotconfig": {}, "blocklylist": []}')

    def test_scripts_without_code_or_script_name_fail(self):
        self.assertRaises(
            ConfigError,
            lambda: RobotConfig.from_string(
                """
        {
            "robotConfig": [],
            "blocklyList": [
                {
                    "assignments": {
                        "buttons": [
                            {"id": 0, "priority": 2},
                            {"id": 2, "priority": 0}
                        ]
                    }
                }
            ]
        }"""
            ),
        )

    def test_scripts_can_be_assigned_to_multiple_buttons(self):
        json = """
        {
            "robotConfig": {},
            "blocklyList": [
                {
                    "pythonCode": "{SOURCE}",
                    "assignments": {
                        "buttons": [
                            {"id": 0, "priority": 2},
                            {"id": 2, "priority": 0}
                        ]
                    }
                }
            ]
        }""".replace(
            "{SOURCE}", b64_encode_str("some code")
        )
        config = RobotConfig.from_string(json)

        script_names = ["script_0_button_0", "script_0_button_2"]

        self.assertEqual(script_names[0], config.controller.buttons[0].name)
        self.assertEqual(script_names[1], config.controller.buttons[2].name)

        self.assertTrue(callable(config.controller.buttons[0].runnable))
        self.assertTrue(callable(config.controller.buttons[2].runnable))

        self.assertEqual(2, config.controller.buttons[0].priority)
        self.assertEqual(0, config.controller.buttons[2].priority)

    def test_assigning_script_to_wrong_button_fails_parsing(self):
        self.assertRaises(
            ConfigError,
            lambda: RobotConfig.from_string(
                """
        {
            "robotConfig": [],
            "blocklyList": [
                {
                    "pythonCode": "",
                    "assignments": {
                        "buttons": [
                            {"id": 33, "priority": 0}
                        ]
                    }
                }
            ]
        }"""
            ),
        )
        self.assertRaises(
            ConfigError,
            lambda: RobotConfig.from_string(
                """
        {
            "robotConfig": [],
            "blocklyList": [
                {
                    "pythonCode": "",
                    "assignments": {
                        "buttons": [
                            {"id": "nan", "priority": 0}
                        ]
                    }
                }
            ]
        }"""
            ),
        )

    def test_scripts_can_be_assigned_to_multiple_analog_channels(self):
        json = """
        {
            "robotConfig": {},
            "blocklyList": [
                {
                    "pythonCode": "{SOURCE}",
                    "assignments": {
                        "analog": [
                            {"channels": [0, 1], "priority": 1}
                        ]
                    }
                }
            ]
        }""".replace(
            "{SOURCE}", b64_encode_str("some code")
        )
        config = RobotConfig.from_string(json)

        self.assertEqual(1, len(config.controller.analog))

        script_name = "script_0_analog_channels_0_1"

        script_descriptor = config.controller.analog[0]["script"]

        self.assertListEqual([0, 1], config.controller.analog[0]["channels"])
        self.assertEqual(script_name, script_descriptor.name)
        self.assertTrue(callable(script_descriptor.runnable))
        self.assertEqual(1, script_descriptor.priority)

    def test_scripts_can_be_configured_to_run_in_background(self):
        json = """
        {
            "robotConfig": {},
            "blocklyList": [
                {
                    "pythonCode": "{SOURCE}",
                    "assignments": {
                        "background": 3
                    }
                }
            ]
        }""".replace(
            "{SOURCE}", b64_encode_str("some code")
        )
        config = RobotConfig.from_string(json)

        self.assertEqual(1, len(config.background_scripts))

        script_name = "script_0_background_0"

        self.assertEqual(script_name, config.background_scripts[0].name)
        self.assertEqual(3, config.background_scripts[0].priority)

    def test_lower_case_pythoncode_is_accepted(self):
        json = """
        {
            "robotConfig": {},
            "blocklyList": [
                {
                    "pythoncode": "{SOURCE}",
                    "assignments": {
                        "background": 3
                    }
                }
            ]
        }""".replace(
            "{SOURCE}", b64_encode_str("some code")
        )
        config = RobotConfig.from_string(json)

        self.assertEqual(1, len(config.background_scripts))

        script_name = "script_0_background_0"

        self.assertEqual(script_name, config.background_scripts[0].name)
        self.assertTrue(callable(config.background_scripts[0].runnable))
        self.assertEqual(3, config.background_scripts[0].priority)

    def test_builtin_scripts_can_be_referenced(self):
        json = """
        {
            "robotConfig": {},
            "blocklyList": [
                {
                    "builtinScriptName": "drive_2sticks",
                    "assignments": {
                        "analog": [{"channels": [0, 1], "priority": 2}]
                    }
                }
            ]
        }"""
        config = RobotConfig.from_string(json)

        script_name = "script_0_analog_channels_0_1"
        self.assertEqual(script_name, config.controller.analog[0]["script"].name)
        self.assertTrue(callable(config.controller.analog[0]["script"].runnable))
        self.assertEqual(drive_2sticks, config.controller.analog[0]["script"].runnable)

    def test_lower_case_script_name_is_accepted(self):
        json = """
        {
            "robotConfig": {},
            "blocklyList": [
                {
                    "builtinscriptname": "drive_2sticks",
                    "assignments": {
                        "analog": [{"channels": [0, 1], "priority": 2}]
                    }
                }
            ]
        }"""
        config = RobotConfig.from_string(json)

        script_name = "script_0_analog_channels_0_1"
        self.assertEqual(script_name, config.controller.analog[0]["script"].name)
        self.assertTrue(callable(config.controller.analog[0]["script"].runnable))
        self.assertEqual(drive_2sticks, config.controller.analog[0]["script"].runnable)

    def test_scripts_can_be_assigned_to_every_type_at_once(self):
        json = """
        {
            "robotConfig": {},
            "blocklyList": [
                {
                    "pythonCode": "{SOURCE}",
                    "assignments": {
                        "buttons": [{"id": 1, "priority": 0}],
                        "analog": [{"channels": [0, 1], "priority": 1}],
                        "background": 3
                    }
                }
            ]
        }""".replace(
            "{SOURCE}", b64_encode_str("some code")
        )
        config = RobotConfig.from_string(json)

        self.assertEqual(1, len(config.background_scripts))

        script_names = [
            "script_0_analog_channels_0_1",
            "script_0_button_1",
            "script_0_background_0",
        ]

        self.assertEqual(script_names[0], config.controller.analog[0]["script"].name)
        self.assertEqual(script_names[1], config.controller.buttons[1].name)
        self.assertEqual(script_names[2], config.background_scripts[0].name)
        self.assertTrue(callable(config.controller.analog[0]["script"].runnable))
        self.assertTrue(callable(config.controller.buttons[1].runnable))
        self.assertTrue(callable(config.background_scripts[0].runnable))
        self.assertEqual(1, config.controller.analog[0]["script"].priority)
        self.assertEqual(0, config.controller.buttons[1].priority)
        self.assertEqual(3, config.background_scripts[0].priority)

    def test_motors_are_parsed_as_list_of_motors(self):
        json = """
        {
            "robotConfig": {
                "motors": [
                    {
                        "name": "M1",
                        "type": 0,
                        "reversed": 0,
                        "side": 0
                    },
                    {
                        "name": "M2",
                        "type": 2,
                        "reversed": 0,
                        "side": 0
                    },
                    {
                        "name": "M3",
                        "type": 2,
                        "reversed": 1,
                        "side": 0
                    },
                    {
                        "name": "M4",
                        "type": 1,
                        "reversed": 1
                    },
                    {
                        "name": "M5",
                        "type": 2,
                        "reversed": 0,
                        "side": 1
                    },
                    {
                        "name": "M6",
                        "type": 2,
                        "reversed": 1,
                        "side": 1
                    }
                ]
            },
            "blocklyList": []
        }"""

        config = RobotConfig.from_string(json)

        self.assertEqual(None, config.motors[0])

        # drivetrain left
        self.assertEqual(ccw_motor(Motors.RevvyMotor), config.motors[1])  # normal left
        self.assertEqual(Motors.RevvyMotor, config.motors[2])  # reversed left

        # drivetrain right
        self.assertEqual(Motors.RevvyMotor, config.motors[4])  # normal right
        self.assertEqual(ccw_motor(Motors.RevvyMotor), config.motors[5])  # reversed right

        self.assertEqual(Motors.RevvyMotor, config.motors[3])  # motor, no 'side', no 'reversed'

        self.assertListEqual([1, 2], config.drivetrain.left)
        self.assertListEqual([4, 5], config.drivetrain.right)

        self.assertNotIn("M1", config.motors.names)  # not configured port does not have name
        self.assertEqual(1, config.motors.names["M2"])
        self.assertEqual(2, config.motors.names["M3"])
        self.assertEqual(3, config.motors.names["M4"])
        self.assertEqual(4, config.motors.names["M5"])
        self.assertEqual(5, config.motors.names["M6"])

    def test_motor_side_and_reversed_is_ignored_for_normal_motors(self):
        json = """
        {
            "robotConfig": {
                "motors": [
                    {
                        "name": "M1",
                        "type": 1,
                        "reversed": 0,
                        "side": 0
                    },
                    {
                        "name": "M2",
                        "type": 1,
                        "reversed": 1,
                        "side": 0
                    },
                    {
                        "name": "M3",
                        "type": 1,
                        "reversed": 0,
                        "side": 1
                    },
                    {
                        "name": "M4",
                        "type": 1,
                        "reversed": 1,
                        "side": 1
                    }
                ]
            },
            "blocklyList": []
        }"""

        config = RobotConfig.from_string(json)

        self.assertEqual(Motors.RevvyMotor, config.motors[0])
        self.assertEqual(Motors.RevvyMotor, config.motors[1])
        self.assertEqual(Motors.RevvyMotor, config.motors[2])
        self.assertEqual(Motors.RevvyMotor, config.motors[3])

    def test_empty_or_null_motors_are_not_configured(self):
        json = """
        {
            "robotConfig": {
                "motors": [
                    {
                        "name": "M1",
                        "type": 1,
                        "side": 0
                    },
                    {},
                    null,
                    {
                        "name": "M4",
                        "type": 1,
                        "side": 1
                    }
                ]
            },
            "blocklyList": []
        }"""

        config = RobotConfig.from_string(json)

        self.assertEqual(Motors.RevvyMotor, config.motors[0])
        self.assertEqual(None, config.motors[1])
        self.assertEqual(None, config.motors[2])
        self.assertEqual(Motors.RevvyMotor, config.motors[3])

    def test_sensors_are_parsed_as_list_of_sensors(self):
        json = """
        {
            "robotConfig": {
                "sensors": [
                    {
                        "name": "S1",
                        "type": 1
                    },
                    {
                        "name": "S2",
                        "type": 2
                    },
                    {
                        "name": "S3",
                        "type": 0
                    },
                    {
                        "name": "S4",
                        "type": 0
                    }
                ]
            },
            "blocklyList": []
        }"""

        config = RobotConfig.from_string(json)

        self.assertEqual(Sensors.Ultrasonic, config.sensors[0])
        self.assertEqual(Sensors.BumperSwitch, config.sensors[1])
        self.assertEqual(None, config.sensors[2])
        self.assertEqual(None, config.sensors[3])

        self.assertEqual(0, config.sensors.names["S1"])
        self.assertEqual(1, config.sensors.names["S2"])
        # not configured ports does not have names
        self.assertNotIn("S3", config.sensors.names)
        self.assertNotIn("S4", config.sensors.names)

    def test_empty_or_null_sensors_are_not_configured(self):
        json = """
        {
            "robotConfig": {
                "sensors": [
                    {
                        "name": "S1",
                        "type": 1
                    },
                    {},
                    null,
                    {
                        "name": "S4",
                        "type": 2
                    }
                ]
            },
            "blocklyList": []
        }"""

        config = RobotConfig.from_string(json)

        self.assertEqual(Sensors.Ultrasonic, config.sensors[0])
        self.assertEqual(None, config.sensors[1])
        self.assertEqual(None, config.sensors[2])
        self.assertEqual(Sensors.BumperSwitch, config.sensors[3])

    def test_type0_objects_dont_require_additional_keys(self):
        json = """
        {
            "robotConfig": {
                "motors": [
                    {
                        "type": 0
                    }
                ],
                "sensors": [
                    {
                        "type": 0
                    }
                ]
            },
            "blocklyList": []
        }"""

        config = RobotConfig.from_string(json)
        self.assertIsNotNone(config)

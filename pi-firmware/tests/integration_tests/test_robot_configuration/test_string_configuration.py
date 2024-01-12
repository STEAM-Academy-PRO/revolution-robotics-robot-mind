# SPDX-License-Identifier: GPL-3.0-only

import unittest

from revvy.robot_config import RobotConfig
from revvy.scripting.robot_interface import PortCollection


class TestPortConfiguration(unittest.TestCase):
    def test_named_ports_can_be_accessed_via_robot_interface(self):
        """This test case verifies that PortCollection and RobotConfig use the same port numbering conventions"""
        config_str = '''{
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
                        "type": 2,
                        "reversed": 1,
                        "side": 1
                    }
                ],
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
                        "type": 1
                    }
                ]
            },
            "blocklyList": []
        }'''
        config = RobotConfig.from_string(config_str)

        motors = PortCollection([2, 3, 5, 7])
        motors.aliases.update(config.motors.names)

        sensors = PortCollection([3, 5, 7, 9])
        sensors.aliases.update(config.sensors.names)

        self.assertEqual(3, motors["M2"])
        self.assertEqual(9, sensors["S4"])

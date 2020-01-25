# SPDX-License-Identifier: GPL-3.0-only

import unittest
from mock import Mock

from revvy.scripting.builtin_scripts import drive_joystick, drive_2sticks

max_speed = 600


def create_mock_robot():
    mock = Mock()
    robot = Mock()
    robot.joystick = Mock()
    robot.joystick.set_speeds = mock
    return mock, robot


class TestJoystickScripts(unittest.TestCase):
    def test_middle_position_is_idle(self):
        mock, robot = create_mock_robot()

        args = {'robot': robot, 'channels': [127, 127]}
        drive_joystick(**args)
        self.assertEqual(1, mock.call_count)
        self.assertEqual((0, 0), mock.call_args[0])

    def test_vertical_position_is_drive(self):
        mock, robot = create_mock_robot()

        args = {'robot': robot, 'channels': [127, 255]}
        drive_joystick(**args)
        self.assertEqual((max_speed, max_speed), mock.call_args[0])

        args = {'robot': robot, 'channels': [127, 0]}
        drive_joystick(**args)
        self.assertEqual((-max_speed, -max_speed), mock.call_args[0])

    def test_horizontal_position_is_turn(self):
        mock, robot = create_mock_robot()

        args = {'robot': robot, 'channels': [0, 127]}
        drive_joystick(**args)
        self.assertEqual((-max_speed, max_speed), mock.call_args[0])

        args = {'robot': robot, 'channels': [255, 127]}
        drive_joystick(**args)
        self.assertEqual((max_speed, -max_speed), mock.call_args[0])


class TestStickDriveScripts(unittest.TestCase):
    def test_middle_position_is_idle(self):
        mock, robot = create_mock_robot()

        args = {'robot': robot, 'channels': [127, 127]}
        drive_2sticks(**args)
        self.assertEqual(1, mock.call_count)
        self.assertEqual((0, 0), mock.call_args[0])

    def test_sticks_control_sides_independently(self):
        mock, robot = create_mock_robot()

        args = {'robot': robot, 'channels': [127, 255]}
        drive_2sticks(**args)
        self.assertEqual((0, max_speed), mock.call_args[0])

        args = {'robot': robot, 'channels': [127, 0]}
        drive_2sticks(**args)
        self.assertEqual((0, -max_speed), mock.call_args[0])

        args = {'robot': robot, 'channels': [255, 127]}
        drive_2sticks(**args)
        self.assertEqual((max_speed, 0), mock.call_args[0])

        args = {'robot': robot, 'channels': [0, 127]}
        drive_2sticks(**args)
        self.assertEqual((-max_speed, 0), mock.call_args[0])

        args = {'robot': robot, 'channels': [255, 255]}
        drive_2sticks(**args)
        self.assertEqual((max_speed, max_speed), mock.call_args[0])

        args = {'robot': robot, 'channels': [0, 0]}
        drive_2sticks(**args)
        self.assertEqual((-max_speed, -max_speed), mock.call_args[0])

import unittest

from mock import Mock, call

from revvy.scripting.resource import Resource
from revvy.scripting.robot_interface import DriveTrainWrapper, MotorConstants, ResourceWrapper


class TestDrivetrainWrapper(unittest.TestCase):
    def test_drive_for_time_calls_set_speeds_rpm(self):
        mock_drivetrain = Mock()
        mock_drivetrain.set_speeds_independent = Mock()

        mock_drivetrain.is_moving = False

        mock_script = Mock()
        mock_script.is_stop_requested = False

        res = ResourceWrapper(Resource(), 1)

        dtw = DriveTrainWrapper(mock_script, mock_drivetrain, res)

        dtw.drive(MotorConstants.DIRECTION_FWD, 3, MotorConstants.UNIT_SEC, 150, MotorConstants.UNIT_SPEED_RPM)

        self.assertEqual(1, mock_drivetrain.set_speeds_independent.call_count)
        self.assertEqual(1, mock_drivetrain.stop_release.call_count)

        self.assertEqual(call(900, 900), mock_drivetrain.set_speeds_independent.call_args_list[0])

    def test_drive_for_time_calls_set_speeds_pwr(self):
        mock_drivetrain = Mock()
        mock_drivetrain.set_speeds_independent = Mock()

        mock_drivetrain.is_moving = False

        mock_script = Mock()
        mock_script.is_stop_requested = False

        res = ResourceWrapper(Resource(), 1)

        dtw = DriveTrainWrapper(mock_script, mock_drivetrain, res)

        dtw.drive(MotorConstants.DIRECTION_FWD, 3, MotorConstants.UNIT_SEC, 75, MotorConstants.UNIT_SPEED_PWR)

        self.assertEqual(1, mock_drivetrain.set_speeds_independent.call_count)
        self.assertEqual(1, mock_drivetrain.stop_release.call_count)

        self.assertEqual(call(900, 900, power_limit=75), mock_drivetrain.set_speeds_independent.call_args_list[0])

    def test_drive_for_rotation_calls_set_position_rpm(self):
        mock_drivetrain = Mock()
        mock_drivetrain.move = Mock()
        mock_drivetrain.motors = []

        mock_drivetrain.is_moving = False

        mock_script = Mock()
        mock_script.is_stop_requested = False

        res = ResourceWrapper(Resource(), 1)

        dtw = DriveTrainWrapper(mock_script, mock_drivetrain, res)

        dtw.drive(MotorConstants.DIRECTION_FWD, 3, MotorConstants.UNIT_ROT, 150, MotorConstants.UNIT_SPEED_RPM)

        self.assertEqual(1, mock_drivetrain.move.call_count)

        self.assertEqual(call(3*360, 3*360, left_speed=900, right_speed=900), mock_drivetrain.move.call_args)

    def test_drive_for_rotation_calls_set_position_pwr(self):
        mock_drivetrain = Mock()
        mock_drivetrain.move = Mock()
        mock_drivetrain.motors = []

        mock_drivetrain.is_moving = False

        mock_script = Mock()
        mock_script.is_stop_requested = False

        res = ResourceWrapper(Resource(), 1)

        dtw = DriveTrainWrapper(mock_script, mock_drivetrain, res)

        dtw.drive(MotorConstants.DIRECTION_FWD, 3, MotorConstants.UNIT_ROT, 75, MotorConstants.UNIT_SPEED_PWR)

        self.assertEqual(1, mock_drivetrain.move.call_count)

        self.assertEqual(call(3*360, 3*360, power_limit=75), mock_drivetrain.move.call_args)

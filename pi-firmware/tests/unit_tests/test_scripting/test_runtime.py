# SPDX-License-Identifier: GPL-3.0-only

import unittest
from threading import Event

from mock import Mock

from revvy.hardware_dependent.sound import SoundControlBase
from revvy.scripting.resource import Resource
from revvy.scripting.robot_interface import RobotInterface
from revvy.scripting.runtime import ScriptManager, ScriptDescriptor
from revvy.utils.functions import str_to_func


class mockobj:
    pass


# noinspection PyMissingConstructor
class MockSound(SoundControlBase):
    def __init__(self):
        pass


def create_robot_mock():

    robot_mock = mockobj()
    robot_mock.resources = {
        'led_ring': Resource(),
        'drivetrain': Resource(),
        'sound': Resource()
    }
    robot_mock.robot = mockobj()
    robot_mock.robot.time = lambda: 0
    robot_mock.robot.motors = []
    robot_mock.robot.sensors = []

    robot_mock.config = mockobj()
    robot_mock.config.motors = mockobj()
    robot_mock.config.motors.__iter__ = lambda: []
    robot_mock.config.motors.names = {}

    robot_mock.config.sensors = mockobj()
    robot_mock.config.sensors.__iter__ = lambda: []
    robot_mock.config.sensors.names = {}

    robot_mock.robot.drivetrain = mockobj()
    robot_mock.robot.drivetrain.turn = lambda *args, **kwargs: None
    robot_mock.robot.drivetrain.drive = lambda *args, **kwargs: None
    robot_mock.robot.sound = MockSound()
    robot_mock.robot.led = mockobj()
    robot_mock.robot.led.count = 0

    robot_mock.robot.imu = mockobj()

    return robot_mock


class TestRuntime(unittest.TestCase):
    def test_string_script_can_access_assigned_variables(self):
        robot_mock = create_robot_mock()

        mock = Mock()

        sm = ScriptManager(robot_mock)
        sm.assign('mock', mock)
        sm.assign('test', self)
        sm.assign('RobotInterface', RobotInterface)
        sm.add_script(ScriptDescriptor('test', str_to_func('''
test.assertIsInstance(robot, RobotInterface)
mock()'''), 0))

        sm['test'].start()
        sm['test'].cleanup()

        self.assertEqual(1, mock.call_count)

    def test_variables_are_passed_to_callable_script_as_args(self):
        robot_mock = create_robot_mock()

        mock = Mock()

        sm = ScriptManager(robot_mock)
        sm.assign('mock', mock)
        sm.assign('test', self)
        sm.assign('RobotInterface', RobotInterface)

        def _script(test, robot, mock, **kwargs):
            test.assertIsInstance(robot, RobotInterface)
            mock()

        sm.add_script(ScriptDescriptor('test', _script, 0))

        sm['test'].start()
        sm['test'].cleanup()

        self.assertEqual(1, mock.call_count)

    def test_string_script_can_access_variables_assigned_after_creation(self):
        robot_mock = create_robot_mock()

        mock = Mock()

        sm = ScriptManager(robot_mock)
        sm.add_script(ScriptDescriptor('test', str_to_func('''
test.assertIsInstance(robot, RobotInterface)
mock()'''), 0))
        sm.assign('mock', mock)
        sm.assign('test', self)
        sm.assign('RobotInterface', RobotInterface)

        sm['test'].start()
        sm['test'].cleanup()

        self.assertEqual(1, mock.call_count)

    def test_script_input_dict_is_passed_as_variables(self):
        robot_mock = create_robot_mock()

        mock = Mock()

        sm = ScriptManager(robot_mock)
        sm.add_script(ScriptDescriptor('test', str_to_func('mock()'), 0))

        script = sm['test']

        script.start(mock=mock)
        script.stop().wait(2)
        self.assertEqual(1, mock.call_count)

        with self.subTest('Input is not remmebered'):
            script.start()  # mock shall not be called again
            script.stop().wait(2)
            self.assertEqual(1, mock.call_count)

        script.cleanup()

    def test_overwriting_a_script_stops_the_previous_one(self):
        robot_mock = create_robot_mock()

        mock = Mock()
        stopped_mock = Mock()

        sm = ScriptManager(robot_mock)
        sm.add_script(ScriptDescriptor('test', str_to_func('''
while not ctx.stop_requested:
    pass
mock()'''), 0))
        sm.assign('mock', mock)

        # first call, make sure the script runs
        sm['test'].on_stopped(stopped_mock)
        sm['test'].start()

        # add second script
        sm.add_script(ScriptDescriptor('test', str_to_func('mock()'), 0))  # stops the first script

        # check that the first script ran and was stopped
        self.assertEqual(1, mock.call_count)
        self.assertEqual(1, stopped_mock.call_count)

        # run and check second script
        sm['test'].on_stopped(stopped_mock)
        sm['test'].start()
        # test that stop also stops a script
        sm['test'].stop()
        sm['test'].cleanup()

        self.assertEqual(2, mock.call_count)
        self.assertEqual(2, stopped_mock.call_count)

    def test_resetting_the_manager_stops_running_scripts(self):
        robot_mock = create_robot_mock()

        stopped_mock = Mock()

        sm = ScriptManager(robot_mock)
        sm.add_script(ScriptDescriptor('test', str_to_func('''
while not ctx.stop_requested:
    pass
'''), 0))
        sm.add_script(ScriptDescriptor('test2', str_to_func('''
while not ctx.stop_requested:
    pass
'''), 0))

        # first call, make sure the script runs
        sm['test'].on_stopped(stopped_mock)
        sm['test2'].on_stopped(stopped_mock)
        sm['test'].start()
        sm['test2'].start()

        sm.reset()

        self.assertEqual(2, stopped_mock.call_count)

    def test_script_can_stop_itself(self):
        robot_mock = create_robot_mock()

        cont = Event()
        mock = Mock()

        sm = ScriptManager(robot_mock)
        sm.add_script(ScriptDescriptor('test', str_to_func('''
while not ctx.stop_requested:
    mock()
    Control.terminate()
    mock()
'''), 0))
        sm.assign('mock', mock)
        sm['test'].on_stopped(cont.set)

        # first call, make sure the script runs
        sm['test'].start().wait()
        if not cont.wait(2):
            self.fail()

        sm.reset()
        self.assertEqual(1, mock.call_count)

    def test_script_can_stop_other_scripts(self):
        robot_mock = create_robot_mock()

        mock1 = Mock()
        mock2 = Mock()

        second_running_evt = Event()

        sm = ScriptManager(robot_mock)
        sm.add_script(ScriptDescriptor('test1', str_to_func('''
mock()
second_running.wait()
while not ctx.stop_requested:
    Control.terminate_all()
'''), 0))
        sm.add_script(ScriptDescriptor('test2', str_to_func('''
second_running.set()
mock()
while not ctx.stop_requested:
    time.sleep(0.01)
'''), 0))
        sm['test1'].assign('mock', mock1)
        sm['test1'].assign('second_running', second_running_evt)
        sm['test2'].assign('second_running', second_running_evt)
        sm['test2'].assign('mock', mock2)

        try:
            # first call, make sure the script runs
            script1_stopped = Event()
            script2_stopped = Event()
            sm['test1'].on_stopped(script1_stopped.set)
            sm['test2'].on_stopped(script2_stopped.set)
            sm['test1'].start()
            sm['test2'].start()

            script1_stopped.wait(1)
            script2_stopped.wait(1)

            # scripts started?
            self.assertEqual(1, mock1.call_count)
            self.assertEqual(1, mock2.call_count)

            # scripts stopped?
            self.assertFalse(sm['test1'].is_running)
            self.assertFalse(sm['test2'].is_running)
        finally:
            sm.reset()

    def test_crashing_script_calls_stopped_handler(self):
        robot_mock = create_robot_mock()

        cont = Event()

        sm = ScriptManager(robot_mock)
        sm.add_script(ScriptDescriptor('test', str_to_func('''raise Excepti'''), 0))
        sm['test'].on_stopped(cont.set)

        # first call, make sure the script runs
        sm['test'].start().wait()
        if not cont.wait(2):
            self.fail("Script.on_stopped handler was not called")

        sm.reset()

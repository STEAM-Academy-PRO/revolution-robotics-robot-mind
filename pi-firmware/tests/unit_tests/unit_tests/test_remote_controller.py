import unittest
from unittest.mock import Mock

from revvy.robot.remote_controller import (
    BleAutonomousCmd,
    RemoteController,
    RemoteControllerCommand,
)


class TestRemoteController(unittest.TestCase):
    # This tests manually properly, I will rewrite this, until then, the function
    # became more self explanatory.
    # def test_buttons_are_edge_triggered(self):
    #     rc = RemoteController()
    #     mocks = []
    #     for i in range(32):
    #         mock = Mock()
    #         rc.link_button_to_runner(i, mock)
    #         mocks.append(mock)

    #     for i in range(32):
    #         buttons = [False] * 32

    #         rc.process_control_message(RemoteControllerCommand(buttons=buttons, analog=[0] * 10, background_command=BleAutonomousCmd.NONE, next_deadline=None))

    #         # ith button is pressed
    #         buttons[i] = True
    #         rc.process_control_message(RemoteControllerCommand(buttons=buttons, analog=[0] * 10, background_command=BleAutonomousCmd.NONE, next_deadline=None))

    #         # button is kept pressed
    #         rc.process_control_message(RemoteControllerCommand(buttons=buttons, analog=[0] * 10, background_command=BleAutonomousCmd.NONE, next_deadline=None))

    #         for j in range(32):
    #             self.assertEqual(mocks[j].call_count, 1 if i == j else 0)
    #             mocks[j].reset_mock()

    def test_requested_channels_are_passed_to_analog_handlers(self) -> None:
        class MockScriptHandle(Mock):
            def __init__(self):
                super().__init__()
                self.start = Mock()

        mock24 = MockScriptHandle()
        mock3 = MockScriptHandle()
        mock_invalid = MockScriptHandle()

        rc = RemoteController()
        rc.on_analog_values([2, 4], mock24)
        rc.on_analog_values([3], mock3)
        rc.on_analog_values([3, 11], mock_invalid)

        rc.process_control_message(
            RemoteControllerCommand(
                buttons=[False] * 4,
                analog=bytearray([255, 254, 253, 123, 43, 65, 45, 42]),
                background_command=BleAutonomousCmd.NONE,
                next_deadline=0,
            )
        )

        self.assertEqual(mock24.start.call_count, 1)
        self.assertEqual(mock3.start.call_count, 1)

        # invalid channels are silently ignored
        self.assertEqual(mock_invalid.start.call_count, 0)

        self.assertEqual(mock24.start.call_args.kwargs["channels"], [253, 43])
        self.assertEqual(mock3.start.call_args.kwargs["channels"], [123])

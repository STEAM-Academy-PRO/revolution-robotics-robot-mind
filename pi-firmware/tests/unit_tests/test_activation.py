# SPDX-License-Identifier: GPL-3.0-only

import unittest
from unittest.mock import Mock

from revvy.utils.activation import EdgeTrigger, ToggleButton


class TestEdgeTrigger(unittest.TestCase):
    def test_missing_callbacks_cause_no_error(self):
        trigger = EdgeTrigger()

        trigger.handle(0)
        trigger.handle(1)
        trigger.handle(2)
        trigger.handle(1)
        trigger.handle(0)

    def test_edge_detection(self):

        rising = Mock()
        falling = Mock()

        trigger = EdgeTrigger()
        trigger.on_rising_edge(rising)
        trigger.on_falling_edge(falling)

        rising.assert_not_called()
        falling.assert_not_called()

        trigger.handle(0)
        trigger.handle(0)
        trigger.handle(0)
        trigger.handle(1)
        trigger.handle(1)
        trigger.handle(1)

        self.assertEqual(rising.call_count, 1)
        falling.assert_not_called()

        trigger.handle(0)
        trigger.handle(0)
        trigger.handle(0)

        self.assertEqual(rising.call_count, 1)
        self.assertEqual(falling.call_count, 1)

    def test_rising_edge_is_triggered_on_increasing_values(self):

        rising = Mock()
        falling = Mock()

        trigger = EdgeTrigger()
        trigger.on_rising_edge(rising)
        trigger.on_falling_edge(falling)

        rising.assert_not_called()

        trigger.handle(1)
        trigger.handle(2)
        trigger.handle(3)

        self.assertEqual(rising.call_count, 3)
        falling.assert_not_called()

        trigger.handle(2)
        trigger.handle(1)
        trigger.handle(0)

        self.assertEqual(rising.call_count, 3)
        self.assertEqual(falling.call_count, 3)


class TestToggle(unittest.TestCase):
    def test_missing_callbacks_cause_no_error(self):
        trigger = ToggleButton()

        trigger.handle(0)
        trigger.handle(1)
        trigger.handle(2)
        trigger.handle(1)
        trigger.handle(0)

    def test_edge_detection(self):

        enable = Mock()
        disable = Mock()

        trigger = ToggleButton()
        trigger.on_enabled(enable)
        trigger.on_disabled(disable)

        enable.assert_not_called()
        disable.assert_not_called()

        trigger.handle(0)
        trigger.handle(0)
        trigger.handle(0)
        trigger.handle(1)
        trigger.handle(1)
        trigger.handle(1)

        self.assertEqual(enable.call_count, 1)
        disable.assert_not_called()

        trigger.handle(0)

        self.assertEqual(enable.call_count, 1)
        disable.assert_not_called()

        trigger.handle(1)

        self.assertEqual(enable.call_count, 1)
        self.assertEqual(disable.call_count, 1)

    def test_toggle_button_ignores_value(self):

        enable = Mock()
        disable = Mock()

        trigger = ToggleButton()
        trigger.on_enabled(enable)
        trigger.on_disabled(disable)

        enable.assert_not_called()
        disable.assert_not_called()

        trigger.handle(1)
        trigger.handle(2)
        trigger.handle(3)

        self.assertEqual(enable.call_count, 1)
        disable.assert_not_called()

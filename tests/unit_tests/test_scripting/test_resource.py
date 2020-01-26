# SPDX-License-Identifier: GPL-3.0-only

import unittest

from mock import Mock

from revvy.scripting.resource import Resource


priority_high = 0
priority_low = 1


class TestResource(unittest.TestCase):
    def test_empty_resource_can_be_taken(self):
        r = Resource()

        handle = r.request()
        self.assertIsNotNone(handle)

    def test_lower_priority_handle_can_be_taken_taken_away(self):
        r = Resource()

        mock = Mock()
        handle = r.request(priority_low, mock)
        handle2 = r.request(priority_high)
        self.assertIsNotNone(handle)
        self.assertEqual(True, handle.is_interrupted)
        self.assertIsNotNone(handle2)
        self.assertEqual(1, mock.call_count)

    def test_higher_priority_handle_can_not_be_taken_taken_away(self):
        r = Resource()

        mock = Mock()
        handle = r.request(priority_high, mock)
        handle2 = r.request(priority_low)
        self.assertIsNotNone(handle)
        self.assertEqual(False, handle.is_interrupted)
        self.assertIsNone(handle2)
        self.assertEqual(0, mock.call_count)

    def test_resource_handle_needed_to_release(self):
        r = Resource()

        handle = r.request(priority_low)
        handle2 = r.request(priority_high)
        r.release(handle)
        handle3 = r.request(priority_low)
        self.assertIsNone(handle3)
        self.assertEqual(False, handle2.is_interrupted)

    def test_lower_priority_can_take_resource_after_higher_priority_releases(self):
        r = Resource()

        handle = r.request(priority_high)
        handle.release()
        handle2 = r.request(priority_low)
        self.assertIsNotNone(handle)
        self.assertEqual(False, handle.is_interrupted)
        self.assertIsNotNone(handle2)

    def test_run_should_only_run_on_active_handle(self):
        r = Resource()

        mock = Mock()

        handle = r.request(priority_low)
        handle2 = r.request(priority_high)

        handle2.run_uninterruptable(mock)
        handle.run_uninterruptable(lambda: self.fail('This should not run'))
        self.assertEqual(1, mock.call_count)

    def test_resource_can_be_retaken_by_same_priority(self):
        r = Resource()

        handle = r.request(priority_high)
        handle2 = r.request(priority_high)

        self.assertIsNotNone(handle)
        self.assertIsNotNone(handle2)

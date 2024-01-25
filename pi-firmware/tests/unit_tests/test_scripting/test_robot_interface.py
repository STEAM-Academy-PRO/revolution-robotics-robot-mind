
import unittest
from mock import Mock

from revvy.utils.functions import hex2rgb
from revvy.scripting.resource import Resource
from revvy.scripting.robot_interface import RingLedWrapper, PortCollection, ResourceWrapper


### This is no longer the case: ring led should turn over, without coding needed.
# class TestRingLed(unittest.TestCase):
#     def test_ring_leds_are_indexed_from_one(self):
#         led_mock = Mock()
#         led_mock.display_user_frame = Mock()
#         led_mock.count = 6

#         led_resource = ResourceWrapper(Resource(), 0)

#         script = Mock()
#         script.is_stop_requested = False

#         rw = RingLedWrapper(script, led_mock, led_resource)
#         self.assertRaises(IndexError, lambda: rw.set(leds=[0], color='#112233'))
#         rw.set(leds=[1], color='#112233')
#         rw.set(leds=[2], color='#112233')
#         rw.set(leds=[3], color='#112233')
#         rw.set(leds=[4], color='#112233')
#         rw.set(leds=[5], color='#112233')
#         rw.set(leds=[6], color='#112233')
#         self.assertRaises(IndexError, lambda: rw.set(leds=[7], color='#112233'))

    def test_ring_led_set_remembers_previous_state(self):
        led_mock = Mock()
        led_mock.display_user_frame = Mock()
        led_mock.count = 6

        led_resource = ResourceWrapper(Resource(), 0)

        script = Mock()
        script.is_stop_requested = False

        rw = RingLedWrapper(script, led_mock, led_resource)
        rw.set(leds=[1], color='#112233')
        self.assertEqual([hex2rgb("#112233"), 0, 0, 0, 0, 0], led_mock.display_user_frame.call_args[0][0])
        self.assertEqual(1, led_mock.display_user_frame.call_count)

        rw.set(leds=[3, 4], color='#223344')
        self.assertEqual(
            [hex2rgb("#112233"), 0, hex2rgb("#223344"), hex2rgb("#223344"), 0, 0],
            led_mock.display_user_frame.call_args[0][0]
        )
        self.assertEqual(2, led_mock.display_user_frame.call_count)


class TestPortCollection(unittest.TestCase):
    def test_ports_can_be_accessed_by_id(self):
        pc = PortCollection([2, 3, 5])

        self.assertEqual(2, pc[1])
        self.assertEqual(3, pc[2])
        self.assertEqual(5, pc[3])
        self.assertRaises(IndexError, lambda: pc[4])

    def test_ports_can_be_accessed_by_name(self):
        # named ports are indexed from 1
        pc = PortCollection([2, 3, 5])
        pc.aliases.update({'foo': 1, 'bar': 2, 'baz': 3})

        self.assertEqual(2, pc['foo'])
        self.assertEqual(3, pc['bar'])
        self.assertEqual(5, pc['baz'])
        self.assertRaises(KeyError, lambda: pc['foobar'])

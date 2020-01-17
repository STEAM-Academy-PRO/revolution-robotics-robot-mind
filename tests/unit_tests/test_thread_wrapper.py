# SPDX-License-Identifier: GPL-3.0-only

import time
import unittest
from threading import Event

from mock import Mock

from revvy.utils.thread_wrapper import ThreadWrapper, ThreadContext


class TestThreadWrapper(unittest.TestCase):
    def test_thread_wrapper_can_be_exited_if_not_started(self):
        tw = ThreadWrapper(lambda: None)
        tw.exit()

    def test_thread_wrapper_can_be_exited_if_started(self):
        mock = Mock()
        tw = ThreadWrapper(lambda x: None)
        tw.on_stopped(mock)
        tw.start()
        tw.exit()

        self.assertEqual(1, mock.call_count)

    def test_stop_requested_is_only_true_while_thread_is_running(self):
        evt = Event()

        tw = ThreadWrapper(lambda x: evt.wait())

        # at first, the thread is not running so it is not stopping
        self.assertFalse(tw.stopping)

        # the thread is running normally, not stopping
        tw.start()
        self.assertFalse(tw.stopping)

        # calling stop() immediately sets stopping to True
        tw.stop()
        self.assertTrue(tw.stopping)

        # allow exiting
        evt.set()

        # when the thread ends, stopping is reset to False, since the thread is not running
        tw.exit()
        self.assertFalse(tw.stopping)

    def test_waiting_for_a_stopped_thread_to_stop_does_nothing(self):
        tw = ThreadWrapper(lambda ctx: None)
        tw.start().wait()
        tw.stop().wait()
        tw.stop().wait()
        tw.exit()

    def test_exiting_a_running_thread_stops_it(self):
        mock = Mock()

        def test_fn(ctx):
            evt = Event()
            ctx.on_stopped(evt.set)
            evt.wait()
            mock()

        tw = ThreadWrapper(test_fn)
        tw.start().wait()
        tw.exit()

        self.assertEqual(1, mock.call_count)

    def test_thread_function_runs_only_once_per_start(self):
        mock = Mock()
        evt = Event()

        def test_fn(context):
            mock()
            evt.set()

        tw = ThreadWrapper(test_fn)

        try:
            for i in range(1, 3):
                with self.subTest('Run #{}'.format(i)):
                    evt.clear()
                    tw.start()
                    if not evt.wait(2):
                        self.fail('Thread function was not executed')

                    self.assertEqual(i, mock.call_count)

        finally:
            tw.exit()

    def test_stop_callbacks_called_when_thread_fn_exits(self):
        evt = Event()

        def test_fn(context):
            pass

        tw = ThreadWrapper(test_fn)

        try:
            for i in range(1, 3):
                with self.subTest('Run #{}'.format(i)):
                    tw.on_stopped(evt.set)
                    evt.clear()
                    tw.start()
                    if not evt.wait(2):
                        self.fail('Thread function has not exited properly')

        finally:
            tw.exit()

    def test_thread_function_receives_stop_signal(self):
        mock = Mock()
        stop_req_mock = Mock()
        thread_started_evt = Event()

        def _dummy_thread_fn(ctx: ThreadContext):
            mock()
            ctx.on_stopped(stop_req_mock)  # stop signal calls callback
            thread_started_evt.set()
            while not ctx.stop_requested:  # stop signal can be polled
                time.sleep(0.001)

        tw = ThreadWrapper(_dummy_thread_fn)

        try:
            tw.start()
            thread_started_evt.wait()
            self.assertEqual(1, mock.call_count)
            tw.stop().wait()

            self.assertEqual(1, stop_req_mock.call_count)
        finally:
            tw.exit()

    def test_thread_function_can_observe_stop_request(self):
        mock = Mock()
        thread_started_evt = Event()

        def _dummy_thread_fn(ctx: ThreadContext):
            thread_started_evt.set()

            evt = Event()
            ctx.on_stopped(evt.set)
            evt.wait()
            mock()

        tw = ThreadWrapper(_dummy_thread_fn)

        try:
            tw.start()
            if not thread_started_evt.wait(2):
                self.fail('Thread function was not executed')
            tw.stop().wait()
            self.assertEqual(1, mock.call_count)
        finally:
            tw.exit()

    def test_callback_is_called_when_thread_stops(self):
        mock = Mock(return_value=None)
        thread_started_evt = Event()

        tw = ThreadWrapper(lambda x: thread_started_evt.set())
        tw.on_stopped(mock)

        try:
            for i in range(3):
                tw.start()
                if not thread_started_evt.wait(2):
                    self.fail('Thread function was not executed')
                tw.stop().wait()
                self.assertEqual(1, mock.call_count)  # callback is cleared if it does not return True
        finally:
            tw.exit()

    def test_sleep_on_context_is_interrupted_when_thread_is_stopped(self):
        tw = ThreadWrapper(lambda ctx: ctx.sleep(10000))
        start_time = time.time()
        tw.start().wait()
        tw.exit()
        self.assertLess(time.time() - start_time, 2)

    def test_exception_stops_properly(self):
        evt = Event()

        def _dummy_thread_fn():  # wrong signature, results in TypeError
            pass

        tw = ThreadWrapper(_dummy_thread_fn)

        try:
            for i in range(1, 3):
                with self.subTest('Run #{}'.format(i)):
                    tw.on_stopped(evt.set)  # set callback first to verify it will be called after clear
                    evt.clear()
                    if not tw.start().wait(2):
                        self.fail('Thread was not started properly')

                    if not evt.wait(2):
                        self.fail('Thread was not stopped properly')
        finally:
            tw.exit()

    def test_exited_thread_can_not_be_restarted(self):
        tw = ThreadWrapper(lambda x: None)

        tw.exit()
        self.assertRaises(AssertionError, tw.start)

    def test_starting_a_stopping_thread_restarts(self):
        mock = Mock()

        running = Event()
        stopping = Event()
        allow_stop = Event()

        def test_fn(ctx):
            mock()
            running.set()

            start = time.time()
            while not ctx.stop_requested:
                time.sleep(0.01)
                if time.time() - start > 2:
                    raise TimeoutError

            # simulate slow stop process
            stopping.set()
            if not allow_stop.wait(2):
                self.fail('Thread was not allowed to stop properly')

        tw = ThreadWrapper(test_fn)

        try:
            # start thread
            tw.start()
            if not running.wait(2):
                self.fail('Thread was not started')
            self.assertEqual(1, mock.call_count)

            # stop thread, simulating slow shutdown
            stop = tw.stop()
            if not stopping.wait(2):
                self.fail('Thread failed to set stopping event')

            # try to restart while still stopping
            evt = tw.start()

            # finish shutdown
            allow_stop.set()
            if not stop.wait(2):
                self.fail('Thread failed to stop')

            # wait for restart
            if not evt.wait(2):
                self.fail('Thread failed to restart')
        finally:
            allow_stop.set()
            # shut down completely
            tw.exit()

        self.assertEqual(2, mock.call_count)

    def test_stopping_a_starting_thread_stops_thread(self):
        mock = Mock()

        def test_fn(ctx):
            evt = Event()
            ctx.on_stopped(evt.set)
            if not evt.wait(2):
                self.fail('Thread stop was not called')
            mock()

        tw = ThreadWrapper(test_fn)

        try:
            # this is a probabilistic failure, false positives may happen still if the implementation is incorrect
            for i in range(1000):
                mock.reset_mock()
                tw.start()
                if not tw.stop().wait(2):
                    self.fail('Failed to stop thread')

                self.assertEqual(1, mock.call_count)
        finally:
            tw.exit()

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

        tw = ThreadWrapper(lambda _: None)
        tw.on_stopped(mock)

        try:
            for i in range(3):
                tw.start()
                tw.stop().wait()
                self.assertEqual(ThreadWrapper.STOPPED, tw.state)
                self.assertNotEqual(0, mock.call_count)
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

    def test_exiting_thread_can_not_be_restarted(self):
        counter = 0

        def thread_func(ctx):
            nonlocal counter
            counter += 1
            while not ctx.stop_requested:
                ctx.sleep(0.1)

        def _try_restart():
            self.assertRaises(AssertionError, tw.start)

        tw = ThreadWrapper(thread_func)
        tw.on_stopped(_try_restart)
        tw.start()

        tw.exit()
        self.assertEqual(1, counter)

    def test_exited_thread_can_not_be_restarted(self):
        tw = ThreadWrapper(lambda x: None)

        tw.exit()
        self.assertRaises(AssertionError, tw.start)

    def test_starting_a_stopping_thread_restarts(self):
        allow_stop = Event()

        def thread_func(ctx):
            try:
                while not ctx.stop_requested:
                    ctx.sleep(0.1)
            except InterruptedError:
                pass
            finally:
                print('Waiting for allow_stop event')
                allow_stop.wait(2)
                allow_stop.clear()
                print('allow_stop event set')

        tw = ThreadWrapper(thread_func)
        tw.start().wait()
        tw.stop()
        tw.start()
        self.assertEqual(ThreadWrapper.STOPPING, tw.state)
        allow_stop.set()

        time.sleep(0.1)
        self.assertEqual(ThreadWrapper.RUNNING, tw.state)

        allow_stop.set()
        tw.exit()

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

                self.assertEqual(ThreadWrapper.STOPPED, tw.state)
                self.assertEqual(1, mock.call_count)
        finally:
            tw.exit()

    def test_start_does_not_raise_if_not_exited(self):
        def test_fn(ctx):
            print('running')

        tw = ThreadWrapper(test_fn)
        try:
            # this is a probabilistic failure, false negatives may happen still if the implementation is incorrect
            start = time.time()
            while time.time() - start < 5:
                for _ in range(10000):
                    tw.start()
        except AssertionError:
            self.fail('start() raised event')
        finally:
            tw.exit()

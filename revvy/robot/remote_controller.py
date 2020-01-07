# SPDX-License-Identifier: GPL-3.0-only

import time
from collections import namedtuple
from threading import Lock, Event

from revvy.utils.activation import EdgeTrigger
from revvy.utils.thread_wrapper import ThreadWrapper, ThreadContext
from revvy.utils.logger import Logger

RemoteControllerCommand = namedtuple('RemoteControllerCommand', ['analog', 'buttons'])


class RemoteController:
    def __init__(self):
        self._log = Logger('RemoteController')
        self._button_mutex = Lock()

        self._analogActions = []
        self._analogStates = []
        self._previousAnalogStates = []
        self._buttonHandlers = [EdgeTrigger() for _ in range(32)]
        self._buttonActions = [lambda: None] * 32
        self._buttonStates = [False] * 32

        self._controller_detected = lambda: None
        self._controller_disappeared = lambda: None

        for i in range(len(self._buttonHandlers)):
            self.reset_button_handler(i)

    def reset_button_handler(self, i):
        handler = self._buttonHandlers[i]

        # make sure we don't trigger anything
        handler.on_rising_edge(lambda: None)
        handler.on_falling_edge(lambda: None)

        handler.handle(1)

        handler.on_rising_edge(lambda btn=i: self._handle_button_pressed(btn))
        handler.on_falling_edge(lambda btn=i: self._handle_button_released(btn))

    def is_button_pressed(self, button_idx):
        with self._button_mutex:
            return self._buttonStates[button_idx]

    def analog_value(self, analog_idx):
        try:
            with self._button_mutex:
                return self._analogStates[analog_idx]
        except IndexError:
            return 0

    def reset(self):
        self._log('RemoteController: reset')
        with self._button_mutex:
            self._analogActions.clear()
            self._analogStates.clear()
            self._previousAnalogStates.clear()

            self._buttonActions = [lambda: None] * 32

            for i in range(len(self._buttonHandlers)):
                self.reset_button_handler(i)

            self._buttonStates = [False] * 32

    def tick(self, message: RemoteControllerCommand):
        # copy states
        with self._button_mutex:
            self._previousAnalogStates = self._analogStates
            self._analogStates = message.analog

        # handle analog channels
        for handler in self._analogActions:
            # check if all channels are present in the message
            try:
                current = [message.analog[x] for x in handler['channels']]
                try:
                    previous = [self._previousAnalogStates[x] for x in handler['channels']]
                except IndexError:
                    previous = []
                if current != [127] * len(current) or current != previous:
                    handler['action'](current)
            except IndexError:
                self._log('Skip analog handler for channels {}'.format(", ".join(map(str, handler['channels']))))

        # handle button presses
        for idx in range(len(self._buttonHandlers)):
            with self._button_mutex:
                self._buttonHandlers[idx].handle(message.buttons[idx])

    def on_button_pressed(self, button, action):
        self._buttonHandlers[button].on_rising_edge(action)

    def on_analog_values(self, channels, action):
        self._analogActions.append({'channels': channels, 'action': action})

    def _handle_button_pressed(self, btn):
        self._buttonStates[btn] = True
        self._buttonActions[btn]()

    def _handle_button_released(self, btn):
        self._buttonStates[btn] = False


class RemoteControllerScheduler:

    first_message_timeout = 2
    message_max_period = 0.5

    def __init__(self, rc: RemoteController):
        self._controller = rc
        self._data_ready_event = Event()
        self._controller_detected_callback = lambda: None
        self._controller_lost_callback = lambda: None
        self._data_mutex = Lock()
        self._message = None
        self._log = Logger('RemoteControllerScheduler')

    def data_ready(self, message: RemoteControllerCommand):
        with self._data_mutex:
            self._message = message
        self._data_ready_event.set()

    def _wait_for_message(self, is_first_message):
        if is_first_message:
            return self._data_ready_event.wait(self.first_message_timeout)
        else:
            return self._data_ready_event.wait(self.message_max_period)

    def handle_controller(self, ctx: ThreadContext):
        self._log('Waiting for controller')

        self._data_ready_event.clear()

        ctx.on_stopped(self._data_ready_event.set)

        # wait for first message
        first = True

        start_time = time.time()
        while self._wait_for_message(first):
            if ctx.stop_requested:
                break

            if first:
                self._log("Time to first message: {}s".format(time.time() - start_time))
                self._controller_detected_callback()
                first = False

            with self._data_mutex:
                message = self._message
            self._data_ready_event.clear()
            self._controller.tick(message)

        if not ctx.stop_requested:
            self._controller_lost_callback()

        # reset here, controller was lost or stopped
        self._controller.reset()
        self._log('exited')

    def on_controller_detected(self, callback):
        self._log('Register controller found handler')
        self._controller_detected_callback = callback

    def on_controller_lost(self, callback):
        self._log('Register controller lost handler')
        self._controller_lost_callback = callback


def create_remote_controller_thread(rcs: RemoteControllerScheduler):
    return ThreadWrapper(rcs.handle_controller, "RemoteControllerThread")

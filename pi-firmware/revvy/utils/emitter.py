""" Simple event emitter lib """

from contextlib import suppress
from typing import Callable, Dict, Generic, List, TypeVar

from revvy.utils.logger import LogLevel, get_logger

CustomEventType = TypeVar('CustomEventType')

log = get_logger('emitter', LogLevel.ERROR)


class SimpleEventEmitter:
    """ A simple event emitter that can be used to subscribe to an event source. """

    def __init__(self):
        self._callbacks: List[Callable] = []

    def is_empty(self):
        return len(self._callbacks) == 0

    def add(self, callback):
        self._callbacks.append(callback)

    def clear(self):
        self._callbacks.clear()

    def remove(self, callback):
        # do not raise an error if the callback is not in the list
        with suppress(ValueError):
            self._callbacks.remove(callback)

    def __contains__(self, item):
        return item in self._callbacks

    def trigger(self, *args, **kwargs):
        for func in self._callbacks:
            func(*args, **kwargs)


class Emitter(Generic[CustomEventType]):
    """ Event emitter base class to inherit from. """

    def __init__(self):
        self._events_handlers: Dict[CustomEventType, SimpleEventEmitter] = {}
        self._all_handlers = SimpleEventEmitter()

    def on(self, event: CustomEventType, callback: Callable):
        """ Subscribe to script runner events """
        if event == 'all':
            self._all_handlers.add(callback)

        if event not in self._events_handlers:
            self._events_handlers[event] = SimpleEventEmitter()

        if callback not in self._events_handlers[event]:
            self._events_handlers[event].add(callback)
        else:
            log("Dev error: Emitter wants to add the same function reference to the same event twice.")

    def off(self, event, callback: Callable):
        """ unsubscribe from event """
        self._events_handlers[event].remove(callback)

    def clear(self):
        self._events_handlers.clear()

    def trigger(self, event_type: CustomEventType, data=None):
        """ Triggers all the event handlers subscribed with on(event, callback) """

        self._all_handlers.trigger(self, event_type, data)

        if event_type not in self._events_handlers:
            # Noone to notify...
            return

        # Important to pass down self, so we have the reference of
        # the handler one level up.
        self._events_handlers[event_type].trigger(self, data)

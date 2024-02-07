""" Simple event emitter lib """

from typing import Callable, Dict, Generic, List, TypeVar

from revvy.utils.logger import LogLevel, get_logger

CustomEventType = TypeVar('CustomEventType')

log = get_logger('emitter', LogLevel.ERROR)


class Emitter(Generic[CustomEventType]):
    """ Simple Emitter class to inherit from. """

    _events_handlers: Dict[CustomEventType, List[Callable]] = {}
    _all_handlers = []

    def on(self, event: CustomEventType, callback):
        """ Subscribe to script runner events """
        if event == 'all':
            self._all_handlers.append(callback)
        if event not in self._events_handlers:
            self._events_handlers[event] = []
        if callback not in self._events_handlers[event]:
            self._events_handlers[event].append(callback)
        else:
            log("Dev error: Emitter wants to add the same function reference to the same event twice.")

    def off(self, event, callback: Callable):
        """ unsubscribe from event """
        self._events_handlers[event].remove(callback)

    def clear(self):
        self._events_handlers.clear()

    def trigger(self, event_type: CustomEventType, data=None):
        """ Triggers all the event handlers subscribed with on(event, callback) """

        for handler in self._all_handlers:
            handler(self, event_type, data)

        if event_type not in self._events_handlers:
            # Noone to notify...
            return
        for event_handler in self._events_handlers[event_type]:
            # Important to pass down self, so we have the reference of
            # the handler one level up.
            event_handler(self, data)


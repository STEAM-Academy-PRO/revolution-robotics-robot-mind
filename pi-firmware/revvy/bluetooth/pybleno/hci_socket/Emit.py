class Emit:
    def __init__(self) -> None:
        self._events = {}

    def on(self, event, handler) -> None:
        self._events = self._events
        handlers = self._events[event] = self._events[event] if event in self._events else []
        handlers.append(handler)

    def off(self, event, handler) -> None:
        handlers = self._events[event] = self._events[event] if event in self._events else []
        handlers.remove(handler)

    def emit(self, event, arguments) -> None:
        # print self._events
        # print self._events[event]
        handlers = self._events[event] if event in self._events else []
        for handler in handlers:
            handler(*arguments)

    def once(self, event, arguments, handler) -> None:
        def temporary_handler(*arguments):
            self.off(event, temporary_handler)
            handler(*arguments)

        self.on(event, temporary_handler)

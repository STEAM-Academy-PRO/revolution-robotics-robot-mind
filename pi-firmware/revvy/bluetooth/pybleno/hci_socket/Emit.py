class Emit:
    def __init__(self) -> None:
        self._events: dict[str, list] = {}

    def on(self, event: str, handler) -> None:
        if event not in self._events:
            self._events[event] = []

        self._events[event].append(handler)

    def off(self, event: str, handler) -> None:
        if event not in self._events:
            return

        self._events[event].remove(handler)

    def emit(self, event: str, arguments) -> None:
        # print self._events
        # print self._events[event]
        if event not in self._events:
            return

        for handler in self._events[event]:
            handler(*arguments)

    def once(self, event: str, arguments, handler) -> None:
        def temporary_handler(*arguments) -> None:
            self.off(event, temporary_handler)
            handler(*arguments)

        self.on(event, temporary_handler)

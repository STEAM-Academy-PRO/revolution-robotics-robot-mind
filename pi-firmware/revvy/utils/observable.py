# Simple observable implementation.


class Observable:
    def __init__(self, value):
        self._value = value
        self._observers = []

    def update(self, value):
        self._value = value
        self._notify_observers(value)

    def get(self):
        return self._value

    def subscribe(self, observer):
        self._observers.append(observer)

    def unsubscribe(self, observer):
        self._observers.remove(observer)

    def _notify_observers(self, new_value):
        for observer in self._observers:
            observer(new_value)


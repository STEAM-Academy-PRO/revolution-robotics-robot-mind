# SPDX-License-Identifier: GPL-3.0-only


class EdgeDetector:
    """
    >>> ed = EdgeDetector()
    >>> print(", ".join(map(str, [ed.handle(1), ed.handle(2), ed.handle(2), ed.handle(1)])))
    1, 1, 0, -1
    """
    def __init__(self):
        self._previous = 0

    def handle(self, value):
        previous, self._previous = self._previous, value

        if value > previous:
            return 1
        elif value < previous:
            return -1
        else:
            return 0


class EdgeTrigger:
    def __init__(self):
        self._rising_edge = None
        self._falling_edge = None
        self._detector = EdgeDetector()

    def on_rising_edge(self, l):
        self._rising_edge = l

    def on_falling_edge(self, l):
        self._falling_edge = l

    def handle(self, value):
        detection = self._detector.handle(value)
        if detection == 1:
            if self._rising_edge:
                self._rising_edge()
        elif detection == -1:
            if self._falling_edge:
                self._falling_edge()


class LevelTrigger:
    def __init__(self):
        self._high = None
        self._low = None

    def on_high(self, l):
        self._high = l

    def on_low(self, l):
        self._low = l

    def handle(self, value):
        if value > 0:
            if self._high:
                self._high()
        else:
            if self._low:
                self._low()


class ToggleButton:
    def __init__(self):
        self._on_enabled = None
        self._on_disabled = None
        self._edge_detector = EdgeDetector()
        self._is_enabled = False

    def _toggle(self):
        self._is_enabled = not self._is_enabled
        if self._is_enabled:
            if self._on_enabled:
                self._on_enabled()
        else:
            if self._on_disabled:
                self._on_disabled()

    def on_enabled(self, l):
        self._on_enabled = l

    def on_disabled(self, l):
        self._on_disabled = l

    def handle(self, value):
        if self._edge_detector.handle(0 if value <= 0 else 1) == 1:
            self._toggle()

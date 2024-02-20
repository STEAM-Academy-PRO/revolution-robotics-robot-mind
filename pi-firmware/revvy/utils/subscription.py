""" Simple type-safe dispose util """

from abc import ABC, abstractmethod
from ctypes import Array


class Disposable(ABC):
    """A list element that has a dispose function to clean up after itself."""

    @abstractmethod
    def dispose(self):
        """Logic to dispose function"""
        pass


class DisposableArray:
    """Collection of sensor data wrappers that can be disposed easily."""

    def __init__(self):
        self._subscriptions: Array[Disposable] = []

    def add(self, subscription: Disposable):
        """Append element to list."""
        self._subscriptions.append(subscription)

    def dispose(self):
        """Remove all the list elements and dispose them all."""
        for reading_subscription in self._subscriptions:
            reading_subscription.dispose()

        self._subscriptions.clear()

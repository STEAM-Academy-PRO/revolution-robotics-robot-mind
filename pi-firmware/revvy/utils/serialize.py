from abc import ABC, abstractmethod


class Serialize(ABC):
    @abstractmethod
    def serialize(self) -> bytes:
        pass

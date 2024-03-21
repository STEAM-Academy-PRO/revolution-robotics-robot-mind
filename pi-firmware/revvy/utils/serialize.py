from typing import Protocol, runtime_checkable


@runtime_checkable
class Serialize(Protocol):
    def __bytes__(self) -> bytes: ...

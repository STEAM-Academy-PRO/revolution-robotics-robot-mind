import array
from typing import Any


class Descriptor:
    def __init__(self, options: dict[str, Any]):
        self.uuid = options["uuid"]
        if options["value"] is str:
            self.value = array.array("B", [ord(c) for c in options["value"]])
        else:
            self.value = options["value"]

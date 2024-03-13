from pybleno import BlenoPrimaryService


class BleService(BlenoPrimaryService):
    """Generic Bluetooth Service Channel Interface"""

    def __init__(self, uuid, characteristics: dict):

        self._named_characteristics = characteristics

        super().__init__({"uuid": uuid, "characteristics": list(characteristics.values())})

    def characteristic(self, item: str):
        """Returns the requested characteristic"""
        return self._named_characteristics[item]

""" Subscribe to the long messages coming via Bluetooth. """

from pybleno import BlenoPrimaryService
from revvy.bluetooth.ble_characteristics import LongMessageCharacteristic
from revvy.bluetooth.longmessage import LongMessageHandler


class LongMessageService(BlenoPrimaryService):
    def __init__(self, handler: LongMessageHandler):
        super().__init__(
            {
                "uuid": "97148a03-5b9d-11e9-8647-d663bd873d93",
                "characteristics": [
                    LongMessageCharacteristic(handler),
                ],
            }
        )

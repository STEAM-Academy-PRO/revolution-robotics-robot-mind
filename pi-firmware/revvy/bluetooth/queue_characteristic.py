"""
   Generic queue characteristic for BLE communication.
   Sends messages as they can be sent, safe to call it
   fast one after the other as it will queue the messages.

   Requires the mobile side to update the content of the attribute
   to OK when received a new message.
"""

from functools import partial
from typing import Callable, Optional
from pybleno import Characteristic, Descriptor

from revvy.utils.logger import get_logger

# When the queue ends but the mobile reads, we send this token to the mobile
# to indicate that the queue is empty.
END_TOKEN = b"_X_"

# When mobile got a packet, it responds with the b'OK' token.
CONFIRM_TOKEN = b"OK"

log = get_logger("BLE Queue")


class QueueCharacteristic(Characteristic):
    """Makes sure the proper sending speed is ok by managing a queue of messages."""

    def __init__(self, uuid: str, description: bytes):
        super().__init__(
            {
                "uuid": uuid,
                "properties": ["read", "write", "notify"],
                "descriptors": [
                    Descriptor({"uuid": "2901", "value": description}),
                ],
            }
        )

        self._on_ready_callback: Optional[Callable] = None
        self._value = END_TOKEN
        self._queue = []

        self.is_sending = False

    def onWriteRequest(self, data, offset, withoutResponse, callback):
        """Mobile sends a confirmation that it got the latest pocket by overwriting the value to confirm."""
        if data == CONFIRM_TOKEN:
            self.is_sending = False
            on_ready_callback = self._on_ready_callback
            if on_ready_callback:
                on_ready_callback()
        callback(Characteristic.RESULT_SUCCESS)

    def onReadRequest(self, offset, callback):
        """Mobile sends a query about the data to the brain."""
        # BLE sends packets of 20 bytes, so we need to split the error message into chunks.
        callback(Characteristic.RESULT_SUCCESS, self._value[offset:])

    def _send(self, value, on_ready_callback: Optional[Callable] = None):
        """Send the error message to the mobile."""
        self._value = value

        log(f"Sending: {value}")

        self.is_sending = True

        self._on_ready_callback = on_ready_callback

        # Notify the pybleno lib that the value has changed.
        # We save this, because this can be called by multiple threads.
        on_value_update_notify_pybleno = self.updateValueCallback
        if on_value_update_notify_pybleno:
            on_value_update_notify_pybleno(value)

    def _on_one_ready(self, on_ready_callback: Callable):
        if on_ready_callback:
            on_ready_callback()
        self._process_queue()

    def _process_queue(self) -> None:
        if len(self._queue) > 0:
            if not self.is_sending:
                (next_value, on_ready_callback) = self._queue.pop()
                self._send(next_value, partial(self._on_one_ready, on_ready_callback))
        else:
            self._send(END_TOKEN)

    def sendQueued(
        self, value: bytes, on_ready_callback: Optional[Callable[[], None]] = None
    ) -> None:
        """Send packet to the mobile."""
        self._queue.append((value, on_ready_callback))
        self._process_queue()

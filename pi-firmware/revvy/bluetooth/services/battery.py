from revvy.bluetooth.services.ble import BleService
from revvy.robot.robot import BatteryStatus
from pybleno import Characteristic, Descriptor


class UnifiedBatteryInfoCharacteristic(Characteristic):
    def __init__(self, uuid, description, initial: BatteryStatus) -> None:
        super().__init__(
            {
                "uuid": uuid,
                "properties": ["read", "notify"],
                "descriptors": [Descriptor({"uuid": "2901", "value": description})],
            }
        )

        self._value = encode_battery(initial)

    def onReadRequest(self, offset, callback) -> None:
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG, None)
        else:
            callback(
                Characteristic.RESULT_SUCCESS,
                self._value,
            )

    def updateValue(self, battery: BatteryStatus) -> None:
        new_value = encode_battery(battery)
        if new_value == self._value:
            return

        self._value = new_value

        update_notified_value = self.updateValueCallback
        if update_notified_value:
            update_notified_value(self._value)


def encode_battery(battery: BatteryStatus) -> list[int]:
    return [
        battery.main,
        battery.chargerStatus,
        battery.motor,
        battery.motor_battery_present,
    ]


class CustomBatteryService(BleService):
    def __init__(self, initial: BatteryStatus):
        super().__init__(
            "180F",
            {
                "unified_battery_status": UnifiedBatteryInfoCharacteristic(
                    "2BED", b"Unified battery status", initial
                ),
            },
        )

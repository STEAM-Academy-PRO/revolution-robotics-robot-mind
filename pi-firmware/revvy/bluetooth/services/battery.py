from revvy.bluetooth.ble_characteristics import UnifiedBatteryInfoCharacteristic
from revvy.bluetooth.services.ble import BleService


class CustomBatteryService(BleService):
    def __init__(self):
        unified_battery_status = UnifiedBatteryInfoCharacteristic("2BED", b"Unified battery staus")

        super().__init__(
            "180F",
            {
                "unified_battery_status": unified_battery_status,
            },
        )

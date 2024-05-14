from revvy.bluetooth.ble_characteristics import UnifiedBatteryInfoCharacteristic
from revvy.bluetooth.services.ble import BleService
from revvy.robot.robot import BatteryStatus


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

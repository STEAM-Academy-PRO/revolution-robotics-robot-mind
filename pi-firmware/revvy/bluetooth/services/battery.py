from revvy.bluetooth.ble_characteristics import CustomBatteryLevelCharacteristic, UnifiedBatteryInfoCharacteristic
from revvy.bluetooth.services.ble import BleService


class CustomBatteryService(BleService):
    def __init__(self):
        main_deprecated = CustomBatteryLevelCharacteristic('2A19', b'Main battery percentage')
        unified_battery_status = UnifiedBatteryInfoCharacteristic('2BED', b'Unified battery staus')
        motor = CustomBatteryLevelCharacteristic('00002a19-0000-1000-8000-00805f9b34fa', b'Motor battery percentage')

        super().__init__('180F', {
            'main_battery': main_deprecated,
            'unified_battery_status': unified_battery_status,
            'motor_battery': motor,
        })

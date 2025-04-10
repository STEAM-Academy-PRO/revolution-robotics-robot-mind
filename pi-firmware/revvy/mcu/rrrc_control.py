from revvy.mcu.commands import *
from revvy.mcu.rrrc_transport import RevvyTransport


class RevvyTransportBase(ABC):
    @abstractmethod
    def create_bootloader_control(self) -> "BootloaderControl":
        pass

    @abstractmethod
    def create_application_control(self) -> "RevvyControl":
        pass


class BootloaderControl:
    def __init__(self, transport: RevvyTransport):
        # These commands map to mcu-bootloader/rrrc/runtime/comm_handlers.c
        self.get_hardware_version = ReadHardwareVersionCommand(transport)
        self.send_init_update = InitializeUpdateCommand(transport)
        self.send_firmware = SendFirmwareCommand(transport)
        self.finalize_update = FinalizeUpdateCommand(transport)
        self.read_firmware_crc = ReadFirmwareCrcCommand(transport)


class RevvyControl:
    def __init__(self, transport: RevvyTransport):
        # These commands map to mcu-firmware/rrrc/runtime/comm_handlers.c
        self.ping = PingCommand(transport)

        self.set_master_status = SetMasterStatusCommand(transport)
        self.set_bluetooth_connection_status = SetBluetoothStatusCommand(transport)
        self.get_hardware_version = ReadHardwareVersionCommand(transport)
        self.get_firmware_version = ReadFirmwareVersionCommand(transport)
        self.read_firmware_crc = ReadFirmwareCrcCommand(transport)
        self.reboot_bootloader = RebootToBootloaderCommand(transport)

        self.get_motor_port_amount = ReadMotorPortAmountCommand(transport)
        self.get_motor_port_types = ReadMotorPortTypesCommand(transport)
        self.set_motor_port_type = SetMotorPortTypeCommand(transport)
        self.set_motor_port_config = SetMotorPortConfigCommand(transport)
        self.set_motor_port_control_value = SetMotorPortControlCommand(transport)
        self.test_motor_on_port = TestMotorOnPortCommand(transport)

        self.get_sensor_port_amount = ReadSensorPortAmountCommand(transport)
        self.get_sensor_port_types = ReadSensorPortTypesCommand(transport)
        self.set_sensor_port_type = SetSensorPortTypeCommand(transport)
        self.write_sensor_port = WriteSensorPortCommand(transport)
        self.read_sensor_info = ReadSensorPortInfoCommand(transport)
        self.test_sensor_on_port = TestSensorOnPortCommand(transport)

        self.ring_led_get_scenario_types = ReadRingLedScenarioTypesCommand(transport)
        self.ring_led_get_led_amount = GetRingLedAmountCommand(transport)
        self.ring_led_set_scenario = SetRingLedScenarioCommand(transport)
        self.ring_led_set_user_frame = SendRingLedUserFrameCommand(transport)

        self.status_updater_reset = McuStatusUpdater_ResetCommand(transport)
        self.status_updater_control = McuStatusUpdater_ControlCommand(transport)
        self.status_updater_read = McuStatusUpdater_ReadCommand(transport)

        self.error_memory_read_count = ErrorMemory_ReadCount(transport)
        self.error_memory_read_errors = ErrorMemory_ReadErrors(transport)
        self.error_memory_clear = ErrorMemory_Clear(transport)
        self.error_memory_test = ErrorMemory_TestError(transport)
        self.orientation_reset = IMUOrientationEstimator_Reset_Command(transport)

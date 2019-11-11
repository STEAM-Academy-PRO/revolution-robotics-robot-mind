# SPDX-License-Identifier: GPL-3.0-only

import unittest

from revvy.mcu.commands import *
from revvy.mcu.rrrc_control import RevvyControl, BootloaderControl


class TestParseStringList(unittest.TestCase):
    # TODO: test and handle cases where length byte and string length don't match up

    def test_empty_string_gives_empty_dict(self):
        data = parse_string_list(b'')
        self.assertEqual(data, {})

    def test_string_is_returned_as_dict_key(self):
        data = parse_string_list(b'\x00\x03foo')
        self.assertEqual(data, {'foo': 0})

    def test_multiple_strings_result_in_multiple_pairs_of_data(self):
        data = parse_string_list(b'\x00\x03foo\x01\x03bar')
        self.assertEqual(data, {'foo': 0, 'bar': 1})


class TestControlCommands(unittest.TestCase):
    def test_revvy_command_instances(self):
        # noinspection PyTypeChecker
        control = RevvyControl(None)

        self.assertIs(PingCommand, type(control.ping))

        self.assertIs(SetMasterStatusCommand, type(control.set_master_status))
        self.assertIs(ReadOperationModeCommand, type(control.read_operation_mode))
        self.assertIs(SetBluetoothStatusCommand, type(control.set_bluetooth_connection_status))
        self.assertIs(ReadHardwareVersionCommand, type(control.get_hardware_version))
        self.assertIs(ReadFirmwareVersionCommand, type(control.get_firmware_version))
        self.assertIs(RebootToBootloaderCommand, type(control.reboot_bootloader))

        self.assertIs(ReadMotorPortAmountCommand, type(control.get_motor_port_amount))
        self.assertIs(ReadMotorPortTypesCommand, type(control.get_motor_port_types))
        self.assertIs(SetMotorPortTypeCommand, type(control.set_motor_port_type))
        self.assertIs(SetMotorPortConfigCommand, type(control.set_motor_port_config))
        self.assertIs(SetMotorPortControlCommand, type(control.set_motor_port_control_value))
        self.assertIs(ReadMotorPortStatusCommand, type(control.get_motor_position))

        self.assertIs(ConfigureDrivetrain, type(control.configure_drivetrain))
        self.assertIs(RequestDifferentialDriveTrainPositionCommand, type(control.set_drivetrain_position))
        self.assertIs(RequestDifferentialDriveTrainSpeedCommand, type(control.set_drivetrain_speed))
        self.assertIs(RequestDifferentialDriveTrainTurnCommand, type(control.drivetrain_turn))

        self.assertIs(ReadSensorPortAmountCommand, type(control.get_sensor_port_amount))
        self.assertIs(ReadSensorPortTypesCommand, type(control.get_sensor_port_types))
        self.assertIs(SetSensorPortTypeCommand, type(control.set_sensor_port_type))
        self.assertIs(SetSensorPortConfigCommand, type(control.set_sensor_port_config))
        self.assertIs(ReadSensorPortStatusCommand, type(control.get_sensor_port_value))

        self.assertIs(ReadRingLedScenarioTypesCommand, type(control.ring_led_get_scenario_types))
        self.assertIs(GetRingLedAmountCommand, type(control.ring_led_get_led_amount))
        self.assertIs(SetRingLedScenarioCommand, type(control.ring_led_set_scenario))
        self.assertIs(SendRingLedUserFrameCommand, type(control.ring_led_set_user_frame))

        self.assertIs(McuStatusUpdater_ResetCommand, type(control.status_updater_reset))
        self.assertIs(McuStatusUpdater_ControlCommand, type(control.status_updater_control))
        self.assertIs(McuStatusUpdater_ReadCommand, type(control.status_updater_read))

    def test_revvy_command_ids(self):
        # noinspection PyTypeChecker
        control = RevvyControl(None)

        self.assertEqual(0, control.ping.command_id)

        self.assertEqual(0x04, control.set_master_status.command_id)
        self.assertEqual(0x06, control.read_operation_mode.command_id)
        self.assertEqual(0x05, control.set_bluetooth_connection_status.command_id)
        self.assertEqual(0x01, control.get_hardware_version.command_id)
        self.assertEqual(0x02, control.get_firmware_version.command_id)
        self.assertEqual(0x0B, control.reboot_bootloader.command_id)

        self.assertEqual(0x10, control.get_motor_port_amount.command_id)
        self.assertEqual(0x11, control.get_motor_port_types.command_id)
        self.assertEqual(0x12, control.set_motor_port_type.command_id)
        self.assertEqual(0x13, control.set_motor_port_config.command_id)
        self.assertEqual(0x14, control.set_motor_port_control_value.command_id)
        self.assertEqual(0x15, control.get_motor_position.command_id)

        self.assertEqual(0x1A, control.configure_drivetrain.command_id)
        self.assertEqual(0x1B, control.set_drivetrain_position.command_id)
        self.assertEqual(0x1B, control.set_drivetrain_speed.command_id)
        self.assertEqual(0x1B, control.drivetrain_turn.command_id)

        self.assertEqual(0x20, control.get_sensor_port_amount.command_id)
        self.assertEqual(0x21, control.get_sensor_port_types.command_id)
        self.assertEqual(0x22, control.set_sensor_port_type.command_id)
        self.assertEqual(0x23, control.set_sensor_port_config.command_id)
        self.assertEqual(0x24, control.get_sensor_port_value.command_id)

        self.assertEqual(0x30, control.ring_led_get_scenario_types.command_id)
        self.assertEqual(0x32, control.ring_led_get_led_amount.command_id)
        self.assertEqual(0x31, control.ring_led_set_scenario.command_id)
        self.assertEqual(0x33, control.ring_led_set_user_frame.command_id)

        self.assertEqual(0x3A, control.status_updater_reset.command_id)
        self.assertEqual(0x3B, control.status_updater_control.command_id)
        self.assertEqual(0x3C, control.status_updater_read.command_id)

    def test_bootloader_command_instances(self):
        # noinspection PyTypeChecker
        control = BootloaderControl(None)

        self.assertIs(ReadOperationModeCommand, type(control.read_operation_mode))
        self.assertIs(ReadHardwareVersionCommand, type(control.get_hardware_version))
        self.assertIs(InitializeUpdateCommand, type(control.send_init_update))
        self.assertIs(SendFirmwareCommand, type(control.send_firmware))
        self.assertIs(FinalizeUpdateCommand, type(control.finalize_update))

    def test_bootloader_command_ids(self):
        # noinspection PyTypeChecker
        control = BootloaderControl(None)

        self.assertEqual(0x06, control.read_operation_mode.command_id)
        # read application crc (0x07) is not implemented
        self.assertEqual(0x01, control.get_hardware_version.command_id)
        self.assertEqual(0x08, control.send_init_update.command_id)
        self.assertEqual(0x09, control.send_firmware.command_id)
        self.assertEqual(0x0A, control.finalize_update.command_id)

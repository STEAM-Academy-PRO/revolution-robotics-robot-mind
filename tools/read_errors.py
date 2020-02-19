#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-only
import argparse
import traceback

from revvy.robot.mcu_error import ErrorType, McuErrorReader
from revvy.robot.robot import Robot
from revvy.utils.version import Version
from tools.utils import parse_cfsr


hw_formats = {
    0: '1.0.0',
    1: '1.0.1',
    2: '2.0.0'
}

fw_formats = {
    0: '0.1.{}',
    1: '0.1.{}',
    2: '0.2.{}'
}

exception_names = [
    'Hard fault',
    'Stack overflow',
    'Assertion failure',
    'Test error',
    'IMU error',
    'I2C error'
]


def format_error(error, installed_fw: Version, only_current=False):
    # noinspection PyBroadException
    try:
        error_type = ErrorType(error[0])
        hw_version = error[1:5]
        fw_version = error[5:9]
        error_data = error[9:]

        if error_type == ErrorType.HardFault:
            pc = int.from_bytes(error_data[0:4], byteorder='little')
            psr = int.from_bytes(error_data[4:8], byteorder='little')
            lr = int.from_bytes(error_data[8:12], byteorder='little')
            cfsr = int.from_bytes(error_data[12:16], byteorder='little')
            dfsr = int.from_bytes(error_data[16:20], byteorder='little')
            hfsr = int.from_bytes(error_data[20:24], byteorder='little')

            details_str = '\n\tPC: 0x{0:X}\tPSR: 0x{1:X}\tLR: 0x{2:X}'.format(pc, psr, lr)
            details_str += '\n\tCFSR: 0x{0:X}\tDFSR: 0x{1:X}\tHFSR: 0x{2:X}'.format(cfsr, dfsr, hfsr)

            cfsr_reasons = parse_cfsr(cfsr)
            if cfsr_reasons:
                details_str += "\n\tReasons:" + "\n\t\t".join(cfsr_reasons)

        elif error_type == ErrorType.StackOverflow:
            task = bytes(error_data).decode("utf-8")
            details_str = f'\nTask: {task}'

        elif error_type == ErrorType.AssertFailure:
            line = int.from_bytes(error_data[0:4], byteorder='little')
            file = bytes(error_data[4:]).decode("utf-8")
            details_str = f'\nFile: {file}, Line: {line}'

        elif error_type == ErrorType.TestError:
            details_str = f'\nData: {error_data}'

        elif error_type == ErrorType.ImuError:
            details_str = ''

        else:
            details_str = f'\nData: {error_data}'

        hw = int.from_bytes(hw_version, byteorder='little')
        fw = int.from_bytes(fw_version, byteorder='little')

        hw_str = hw_formats[hw]
        fw_str = fw_formats[hw].format(fw)

        try:
            exception_name = exception_names[error_type.value]
        except IndexError:
            exception_name = 'Unknown error'

        if Version(fw_str) == installed_fw:
            error_template = '{} ({}, HW: {}, FW: {})\nDetails: {}'
        elif not only_current:
            error_template = '{} ({}, HW: {}, FW: {} (NOT CURRENT))\nDetails: {}'
        else:
            return None

        return error_template.format(exception_name, error_type.value, hw_str, fw_str, details_str)

    except Exception:
        traceback.print_exc()
        return f'Error during processing\nRaw data: {error}'


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--inject-test-error', help='Record an error', action='store_true')
    parser.add_argument('--clear', help='Clear the error memory', action='store_true')
    parser.add_argument('--only-current',
                        help='Only display errors that were recorded with the current firmware',
                        action='store_true')

    args = parser.parse_args()

    with Robot() as robot:
        robot_control = robot.robot_control

        current_hw_version = robot_control.get_hardware_version()
        current_fw_version = robot_control.get_firmware_version()
        print(f'Current version numbers: HW: {current_fw_version} FW: {current_fw_version}')

        if args.inject_test_error:
            print('Recording a test error')
            robot_control.error_memory_test()

        error_reader = McuErrorReader(robot_control)

        # read errors
        error_count = error_reader.count
        if error_count == 0:
            print('There are no errors stored')
        elif error_count == 1:
            print('There is one error stored')
        else:
            print(f'There are {error_count} errors stored')

        for i, error_entry in enumerate(error_reader.read_all()):
            formatted_error = format_error(error_entry, current_fw_version, only_current=args.only_current)
            if formatted_error is not None:
                print('----------------------------------------')
                print(f'Error {i}')
                print(formatted_error)

        if args.clear:
            error_reader.clear()

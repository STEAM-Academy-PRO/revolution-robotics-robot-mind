#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-only
import argparse
import enum
import traceback

from revvy.hardware_dependent.rrrc_transport_i2c import RevvyTransportI2C
from revvy.mcu.rrrc_control import RevvyControl
from revvy.utils.version import Version
from tools.utils import parse_cfsr


class ErrorType(enum.IntEnum):
    HardFault = 0
    StackOverflow = 1
    AssertFailure = 2
    TestError = 3
    ImuError = 4


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
        error_id = error[0]
        hw_version = error[1:5]
        fw_version = error[5:9]
        error_data = error[9:]

        if error_id == ErrorType.HardFault:
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
                details_str += "\n\tReasons:"
                for reason in cfsr_reasons:
                    details_str += "\n\t\t" + reason

        elif error_id == ErrorType.StackOverflow:
            task = bytes(error_data).decode("utf-8")
            details_str = '\nTask: {}'.format(task)

        elif error_id == ErrorType.AssertFailure:
            line = int.from_bytes(error_data[0:4], byteorder='little')
            file = bytes(error_data[4:]).decode("utf-8")
            details_str = '\nFile: {}, Line: {}'.format(file, line)

        elif error_id == ErrorType.TestError:
            details_str = '\nData: {}'.format(error_data)

        elif error_id == ErrorType.ImuError:
            details_str = ''

        else:
            details_str = '\nData: {}'.format(error_data)

        hw = int.from_bytes(hw_version, byteorder='little')
        fw = int.from_bytes(fw_version, byteorder='little')

        hw_str = hw_formats[hw]
        fw_str = fw_formats[hw].format(fw)

        try:
            exception_name = exception_names[error_id]
        except IndexError:
            exception_name = 'Unknown error'

        if Version(fw_str) == installed_fw:
            error_template = '{} ({}, HW: {}, FW: {})\nDetails: {}'
        elif not only_current:
            error_template = '{} ({}, HW: {}, FW: {} (NOT CURRENT))\nDetails: {}'
        else:
            return None

        return error_template.format(exception_name, error_id, hw_str, fw_str, details_str)

    except Exception:
        traceback.print_exc()
        return 'Error during processing\nRaw data: {}'.format(error)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--inject-test-error', help='Record an error', action='store_true')
    parser.add_argument('--clear', help='Clear the error memory', action='store_true')
    parser.add_argument('--only-current',
                        help='Only display errors that were recorded with the current firmware',
                        action='store_true')

    args = parser.parse_args()

    with RevvyTransportI2C() as transport:
        robot_control = RevvyControl(transport.bind(0x2D))

        current_hw_version = robot_control.get_hardware_version()
        current_fw_version = robot_control.get_firmware_version()
        print('Current version numbers: HW: {} FW: {}'.format(current_fw_version, current_fw_version))

        if args.inject_test_error:
            print('Recording a test error')
            robot_control.error_memory_test()

        # read errors
        error_count = robot_control.error_memory_read_count()
        if error_count == 0:
            print('There are no errors stored')
        elif error_count == 1:
            print('There is one error stored')
        else:
            print('There are {} errors stored'.format(error_count))

        remaining = error_count
        i = 0
        while remaining > 0:
            errors = robot_control.error_memory_read_errors(i)
            if len(errors) == 0:
                print('0 errors returned, exiting')
                break

            remaining -= len(errors)

            for error_entry in errors:
                formatted_error = format_error(error_entry, current_fw_version, only_current=args.only_current)
                if formatted_error is not None:
                    print('----------------------------------------')
                    print('Error {}'.format(i))
                    print(formatted_error)
                i += 1

        if args.clear:
            print('Clearing error memory...')
            robot_control.error_memory_clear()
            print('Error memory cleared')

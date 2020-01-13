#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-only
import argparse
import sys
import time

from revvy.utils.functions import read_json
from revvy.hardware_dependent.rrrc_transport_i2c import RevvyTransportI2C
from revvy.mcu.rrrc_control import RevvyControl
from revvy.utils.thread_wrapper import periodic
from revvy.robot.robot import Robot

if __name__ == "__main__":

    port_choices = ['Ultrasonic', 'Button', 'EV3', 'EV3_Color']
    port_config_map = {
        'Ultrasonic': 'HC_SR04',
        'Button':     'BumperSwitch',
        'EV3':        'EV3',
        'EV3_Color':  'EV3_Color',
    }

    parser = argparse.ArgumentParser()
    parser.add_argument('--s1', help='Configure S1', default=None, choices=port_choices)
    parser.add_argument('--s2', help='Configure S2', default=None, choices=port_choices)
    parser.add_argument('--s3', help='Configure S3', default=None, choices=port_choices)
    parser.add_argument('--s4', help='Configure S4', default=None, choices=port_choices)
    parser.add_argument('--imu-angle', help='Read IMU yaw angle', action='store_true')

    args = parser.parse_args()

    if not (args.s1 or args.s2 or args.s3 or args.s4 or args.imu_angle):
        print('No ports configured')
        sys.exit(0)

    pattern = "{0:0.2f}"
    if args.s1:
        pattern += "\t{1}"
    if args.s2:
        pattern += "\t{2}"
    if args.s3:
        pattern += "\t{3}"
    if args.s4:
        pattern += "\t{4}"
    if args.imu_angle:
        pattern += "\t{5}"

    sensor_data_changed = False
    sensor_data = [0, None, None, None, None, None]

    with Robot() as robot:
        manifest = read_json('manifest.json')

        def update():
            global sensor_data_changed
            sensor_data_changed = False
            robot.update_status()

            if args.imu_angle:
                angle = robot.imu.yaw_angle
                if angle != sensor_data[5]:
                    sensor_data[5] = angle
                    sensor_data_changed = True

            if sensor_data_changed:
                sensor_data[0] = round(time.time() - robot.start_time, 2)
                print(pattern.format(*sensor_data))

        def sensor_value_changed(idx, value):
            global sensor_data_changed
            if value != sensor_data[idx]:
                sensor_data[idx] = value
                sensor_data_changed = True

        def configure_sensor(index, name):
            sensor = robot.sensors[index]
            sensor.configure(port_config_map[name])
            sensor.on_value_changed(lambda p: sensor_value_changed(index, p.value))

        robot.reset()
        status_update_thread = periodic(update, 0.02, "RobotStatusUpdaterThread")
        status_update_thread.start()

        if args.s1:
            configure_sensor(1, args.s1)
        if args.s2:
            configure_sensor(2, args.s2)
        if args.s3:
            configure_sensor(3, args.s3)
        if args.s4:
            configure_sensor(4, args.s4)

        print('Press Enter to stop')
        input()
        status_update_thread.exit()

#!/usr/bin/python3
import argparse
import sys
from revvy.firmware_updater import update_firmware_if_needed

from revvy.hardware_dependent.rrrc_transport_i2c import RevvyTransportI2C
from revvy.robot.configurations import Sensors
from revvy.robot_manager import RevvyStatusCode
from revvy.utils.thread_wrapper import periodic
from revvy.robot.robot import Robot

if __name__ == "__main__":

    port_config_map = {
        "Ultrasonic": Sensors.Ultrasonic,
        "Button": Sensors.BumperSwitch,
        "Softeq_CS": Sensors.SofteqCS,
    }

    parser = argparse.ArgumentParser()
    parser.add_argument("--s1", help="Configure S1", default=None, choices=port_config_map.keys())
    parser.add_argument("--s2", help="Configure S2", default=None, choices=port_config_map.keys())
    parser.add_argument("--s3", help="Configure S3", default=None, choices=port_config_map.keys())
    parser.add_argument("--s4", help="Configure S4", default=None, choices=port_config_map.keys())
    parser.add_argument("--imu-yaw", help="Read IMU yaw angle", action="store_true")
    parser.add_argument("--raw-imu", help="Read raw IMU acceleration", action="store_true")
    parser.add_argument("--raw-gyro", help="Read raw IMU rotation", action="store_true")
    parser.add_argument("--imu", help="Read IMU orientation angles", action="store_true")

    args = parser.parse_args()

    if not (
        args.s1
        or args.s2
        or args.s3
        or args.s4
        or args.imu_yaw
        or args.raw_imu
        or args.raw_gyro
        or args.imu
    ):
        print("No ports configured")
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
    if args.imu_yaw:
        pattern += "\t{5}"
    if args.raw_imu:
        pattern += "\t{6}"
    if args.raw_gyro:
        pattern += "\t{7}"
    if args.imu:
        pattern += "\t{8}"

    sensor_data_changed = False
    sensor_data = [0, None, None, None, None, None, None, None, None]

    interface = RevvyTransportI2C(bus=1)

    ### Before we enter the main loop, let's load up
    if not update_firmware_if_needed(interface):
        # exiting with integrity error forces the loader to try a previous package
        sys.exit(RevvyStatusCode.INTEGRITY_ERROR)

    robot = Robot(interface)

    def update() -> None:
        global sensor_data_changed
        sensor_data_changed = False
        robot.update_status()

        if args.imu_yaw:
            angle = robot.imu.yaw_angle
            if angle != sensor_data[5]:
                sensor_data[5] = angle
                sensor_data_changed = True

        if args.raw_imu:
            angle = robot.imu.acceleration
            if angle != sensor_data[6]:
                sensor_data[6] = angle
                sensor_data_changed = True

        if args.raw_gyro:
            angle = robot.imu.rotation
            if angle != sensor_data[7]:
                sensor_data[7] = angle
                sensor_data_changed = True

        if args.imu:
            angle = robot.imu.orientation
            if angle != sensor_data[8]:
                sensor_data[8] = angle
                sensor_data_changed = True

        if sensor_data_changed:
            sensor_data[0] = round(robot.time(), 2)
            print(pattern.format(*sensor_data), "\n")

    def sensor_value_changed(idx, value) -> None:
        global sensor_data_changed
        if value != sensor_data[idx]:
            sensor_data[idx] = value
            sensor_data_changed = True

    def configure_sensor(index, name) -> None:
        sensor = robot.sensors[index]
        sensor.configure(port_config_map[name])
        sensor.driver.on_status_changed.add(lambda p: sensor_value_changed(index, p.value))

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

    print("Press Enter to stop")
    input()
    status_update_thread.exit()

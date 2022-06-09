# SPDX-License-Identifier: GPL-3.0-only
import struct
import time

from math import sqrt

from revvy.scripting.robot_interface import DriveTrainWrapper, SensorPortWrapper, rgb_to_hsv
from revvy.utils.functions import clip, map_values
from revvy.scripting.controllers import stick_controller, joystick


def normalize_analog(b):
    """
    >>> normalize_analog(0)
    -1.0
    >>> normalize_analog(255)
    1.0
    >>> normalize_analog(127)
    0.0
    """
    return clip((b - 127) / 127.0, -1.0, 1.0)


def drive(drivetrain_control: DriveTrainWrapper, channels, controller):
    x = normalize_analog(channels[0])
    y = normalize_analog(channels[1])

    sl, sr = controller(x, y)

    drivetrain_control.set_speeds(
        map_values(sl, 0, 1, 0, 120),
        map_values(sr, 0, 1, 0, 120))


def drive_joystick(robot, channels, **_):
    drive(robot.drivetrain, channels, joystick)


def drive_2sticks(robot, channels, **_):
    drive(robot.drivetrain, channels, stick_controller)


class ColorHSV:
    def __init__(self, hue, saturation, value):
        self.hue = hue
        self.saturation = saturation
        self.value = value

    @property
    def h(self):
        return self.hue

    @property
    def s(self):
        return self.saturation

    @property
    def v(self):
        return self.value


def drive_color(drivetrain_control: DriveTrainWrapper, robot_sensors: SensorPortWrapper):
    """ need to set correct line and background colors """
    base_color = 20.3   # 14.5
    background_color_c = 60  # 61.0
    background_color_f = 61.7  # 59.0
    background_color_l = 58.4  # 58.0
    background_color_r = 60  # 56.1
    delta_base_background = 40
    base_speed = 0.35  # 0.33  # 0.3
    count = 0

    k_speed = 1 - 0.33 * base_speed
    if k_speed > 0.99:
        k_speed = 0.99
    k_angle = 5.0

    while count < 500:  # 800:
        count += 1
        # get colors
        res = robot_sensors["RGB"].read()
        sensors = [rgb_to_hsv(*_) for _ in struct.iter_unpack("<BBB", res)]
        # print(sensors)
        forward = sensors[0][0]
        left = 0.76 * sensors[1][0]  # each sensor gives some difference, need to correct
        right = sensors[2][0]
        center = sensors[3][0]
        print(forward, left, right, center)

        # check: stop when line loosed and exit from function
        if abs(background_color_f-forward) < 7 and abs(background_color_c-center) < 7 \
                and abs(background_color_r-right) < 7 and abs(background_color_l-left) < 7:
            drivetrain_control.set_speeds(
                map_values(0, 0, 1, 0, 120),
                map_values(0, 0, 1, 0, 120))
            print("stop, line loosed")
            return 1

        sl = base_speed
        sr = base_speed
        delta_lr = abs(right-left)
        delta = delta_base_background*1.03

        k_diff = (1-k_speed) \
                + k_speed*((k_angle*sqrt(delta-delta_lr)+(delta_base_background-k_angle*sqrt(delta))) / delta)
        print("   k_diff", k_diff, "\n   k_speed", k_speed)
        speed_primary = base_speed * k_diff
        speed_secondary = base_speed / k_diff

        """ red line (17), light background (70)
            if forward sensor at line """
        if abs(base_color-forward) < 55:
            compare = delta_base_background/20
            if delta_lr > compare:
                sr = speed_primary
                sl = speed_secondary
                print("!!!!!!  at right!!")
                if right > left:
                    sl = speed_primary
                    sr = speed_secondary
                    print("++++++  at left!!")
            # check overspeed
            if sl > 1:
                sl = 1
            if sr > 1:
                sr = 1
            # set calculated speeds
            drivetrain_control.set_speeds(
                map_values(sl, 0, 1, 0, 120),
                map_values(sr, 0, 1, 0, 120))
        else:
            print("_________________need to turn")
            # drivetrain_control.set_speeds(
            #     map_values(sl, 0, 1, 0, 120),
            #     map_values(sr, 0, 1, 0, 120))
            # turn right/left straight now
        # wait
        time.sleep(0.015)
    # stop at end of function
    drivetrain_control.set_speeds(
        map_values(0, 0, 1, 0, 120),
        map_values(0, 0, 1, 0, 120))
    return 0


def drive_line(robot, **_):
    drive_color(robot.drivetrain, robot.sensors)


builtin_scripts = {
    'drive_2sticks': drive_2sticks,
    'drive_joystick': drive_joystick,
    'drive_line': drive_line,
}

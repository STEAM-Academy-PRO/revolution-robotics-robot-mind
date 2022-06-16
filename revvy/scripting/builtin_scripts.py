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


def detect_line_background_colors(fd, ct, lt, rt):
    line = 1
    background = 1
    if abs(1 - fd/ct) < 0.2 and abs(1 - lt/rt) < 0.2:
        line = (fd+ct)/2
        background = (lt+rt)/2
        return line, background
    return line, background


def drive_color(drivetrain_control: DriveTrainWrapper, robot_sensors: SensorPortWrapper):
    """ need to set correct line and background colors """
    base_color = 20.3  # 14.5
    background_color = 50
    # background_color_c = 60  # 61.0
    # background_color_f = 61.7  # 59.0
    # background_color_l = 58.4  # 58.0
    # background_color_r = 60  # 56.1
    # delta_base_background = 40
    base_speed = 0.2  # 0.33  # 0.3
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
        print(sensors)
        forward = sensors[0][0]
        left = 0.76 * sensors[1][0]  # each sensor gives some difference, need to correct
        right = sensors[2][0]
        center = sensors[3][0]
        color_max = max(forward, left, right, center)
        color_min = min(forward, left, right, center)
        if color_max > background_color:
            background_color = color_max
        if color_min < base_color:
            base_color = color_min
        delta_base_background = background_color - base_color

        line, background = detect_line_background_colors(forward, center, left, right)
        print(line, background)
        # print(detect_line_background_colors(forward, left, right, center))
        print(forward, left, right, center, base_color, background_color)

        # check: stop when line loosed and exit from function
        # if abs(background_color-forward) < 7 and abs(background_color-center) < 7 \
        #         and abs(background_color-right) < 7 and abs(background_color-left) < 7:
        if not (abs(base_color - forward) < 7 or abs(base_color - center) < 7
                or abs(base_color - right) < 7 or abs(base_color - left) < 7):
            # print("")
            # else:
            drivetrain_control.set_speeds(
                map_values(0, 0, 1, 0, 120),
                map_values(0, 0, 1, 0, 120))
            print("stop, line loosed")
            return 1

        sl = base_speed
        sr = base_speed
        delta_lr = abs(right - left)
        delta = delta_base_background * 1.03

        k_diff = (1 - k_speed) \
                 + k_speed * ((k_angle * sqrt(delta - delta_lr) + (
                    delta_base_background - k_angle * sqrt(delta))) / delta)
        print("   k_diff", k_diff, "\n   k_speed", k_speed)
        speed_primary = base_speed * k_diff
        speed_secondary = base_speed / k_diff

        """ red line (17), light background (70)
            if forward sensor at line """
        if abs(base_color - forward) < 200:  # 55:
            compare = delta_base_background / 20
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

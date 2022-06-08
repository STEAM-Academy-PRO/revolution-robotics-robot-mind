# SPDX-License-Identifier: GPL-3.0-only
import struct
import time

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


def drive_color(drivetrain_control: DriveTrainWrapper, robot_sensors: SensorPortWrapper, controller):
    base_color = 20.3   # 14.5
    background_color_c = 60  # 61.0
    background_color_f = 61.7  # 59.0
    background_color_l = 58.4  # 58.0
    background_color_r = 60  # 56.1
    base_color_delta = background_color_c - base_color
    base_speed = 0.3  # 0.3
    count = 0

    while count < 300:  # 800:
        count += 1

        # get colors
        res = robot_sensors["RGB"].read()
        li = [rgb_to_hsv(*_) for _ in struct.iter_unpack("<BBB", res)]
        # print(li)
        forward = li[0][0]  # round(li[0][0], 1)
        left = 0.76 * li[1][0]  # round(li[1][0], 1)
        right = li[2][0]  # round(li[2][0], 1)
        center = li[3][0]  # round(li[3][0], 1)
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
        k_lr = abs(base_color_delta * 3.30 - delta_lr) / (base_color_delta * 3.30)
        k_diff = k_lr * (1.01 - base_speed) * 1.4  # * 1.15  # k_lr*base_speed*2
        print("k_lr:", round(k_lr, 2), "k_diff:", round(k_diff, 2), "delta_lr:", delta_lr)
        if k_diff > 0.99:
            print("\n\n")
            k_diff = 0.99

        speed_primary = base_speed * k_diff
        # val = (0.1 + (60 - delta_lr) / 100 + k_diff / 2.8)
        val = k_diff * (100 - delta_lr) / 100
        if val > 1:
            print("\n\n")
        print(val, (100 - delta_lr) / 100, k_diff / 2.8)
        speed_secondary = base_speed / val
        # speed_secondary = base_speed / k_diff
        print("primary:", speed_primary, "secondary", speed_secondary)

        """ red line (17), light background (70)
            if forward sensor at line """
        if abs(base_color-forward) < 55:
            if delta_lr > 3:
                if right > left:
                    sl = speed_primary
                    print("to left!!  left-center:", round(left - center, 1))
                    # if abs(base_color - forward) > 3:
                    if delta_lr > 8:
                        sr = speed_secondary
                        print("!!!+++turn left DoubleWells=== ")
                elif right < left:
                    sr = speed_primary
                    print("     to right!!  right-center:", round(right - center, 1))
                    # if abs(base_color - forward) > 3:
                    if delta_lr > 8:
                        sl = speed_secondary
                        print("      !!!+++turn right DoubleWells=== ")
            # set calculated speeds
            if sl > 1:
                sl = 1
            if sr > 1:
                sr = 1
            drivetrain_control.set_speeds(
                map_values(sl, 0, 1, 0, 120),
                map_values(sr, 0, 1, 0, 120))
        else:
            print("_________________need to turn")
            # drivetrain_control.set_speeds(
            #     map_values(sl, 0, 1, 0, 120),
            #     map_values(sr, 0, 1, 0, 120))
            # turn right/left straight no

        # wait
        time.sleep(0.02)
    # stop at end of function
    drivetrain_control.set_speeds(
        map_values(0, 0, 1, 0, 120),
        map_values(0, 0, 1, 0, 120))


def drive_line(robot, **_):
    drive_color(robot.drivetrain, robot.sensors, joystick)


builtin_scripts = {
    'drive_2sticks': drive_2sticks,
    'drive_joystick': drive_joystick,
    'drive_line': drive_line,
}

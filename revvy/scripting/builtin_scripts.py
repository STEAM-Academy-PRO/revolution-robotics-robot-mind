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


def detect_line_background_colors(sensors):
    res = [[], [], []]  # [H] [S] [V]
    grey = []
    for sensor in sensors:
        res[0].append(sensor[0])
        res[1].append(sensor[1])
        res[2].append(sensor[2])
        grey.append(sensor[3])
    print(res)
    delta = []   # searching of most signed from H S V
    for _ in res:
        delta.append(max(_) - min(_))
    i = delta.index(max(delta))
    """next commented  is for using most heavy from H,S,V"""
    # maximum = max(res[i])
    # minimum = min(res[i])
    # background = minimum
    # line = maximum
    # if res[i].index(maximum) in (1, 2):   # then the value of background color is max and line is min
    #     background = maximum
    #     line = minimum
    # print(i, res[i], )
    """grey color using at the time of following is most effective,
       in this case we use HSV just for make decision which way be the next"""
    maxi = max(grey)
    mini = min(grey)
    background = mini
    line = maxi
    if grey.index(maxi) in (1, 2):
        background = maxi
        line = mini

    return line, background, i, tuple(grey), tuple(res[i])


def drive_color(drivetrain_control: DriveTrainWrapper, robot_sensors: SensorPortWrapper):
    """ need to set correct line and background colors, this colors we need to get from search_color function
    it is function for step 3"""
    base_speed = 0.2
    count = 0

    k_speed = 1 - 0.23 * base_speed
    if k_speed > 0.99:
        k_speed = 0.99

    res = robot_sensors["RGB"].read()
    sensors = [rgb_to_hsv(*_) for _ in struct.iter_unpack("<BBB", res)]
    base_color, background_color, i, colors, colors_grey = detect_line_background_colors(sensors)

    while count < 500:  # 800:
        count += 1
        # get colors
        res = robot_sensors["RGB"].read()
        sensors = [rgb_to_hsv(*_) for _ in struct.iter_unpack("<BBB", res)]
        base_color_, background_color_, i, colors_grey, colors = detect_line_background_colors(sensors)
        if base_color < background_color:
            base_color = min(base_color_, base_color)
            background_color = max(background_color_, background_color)
        else:
            base_color = max(base_color_, base_color)
            background_color = min(background_color_, background_color)

        forward, left, right, center = colors_grey
        print("   ", base_color, background_color, "___", forward, left, right, center, "i:", i, colors)

        delta_base_background = abs(background_color - base_color)
        delta = delta_base_background * 1.03

        # check: stop when line loosed and exit from function
        param = delta_base_background * 0.4
        if not (abs(base_color - forward) < param or abs(base_color - center) < param
                or abs(base_color - right) < param or abs(base_color - left) < param):
            drivetrain_control.set_speeds(
                map_values(0, 0, 1, 0, 120),
                map_values(0, 0, 1, 0, 120))
            print("stop, line loosed")
            return 1

        forward_level = 0.35  #  0.40 good for base_speed = 0.2
        k_forward = 0
        temp = abs(forward - base_color) / delta_base_background
        if temp > 0.25:
            k_forward = forward_level * temp
        k_angle = 1.02 + sqrt(delta_base_background / 6.8)  # 7.0 good for base_speed = 0.2
        sl = base_speed
        sr = base_speed
        delta_lr = abs(right - left)
        print("delta:", delta, "delta_lr:", delta_lr, "k_angle:", k_angle, "k_forward:", k_forward)

        k_diff = (1 - k_speed) \
                 + k_speed * ((k_angle * sqrt(abs(delta - delta_lr)) + (
                    delta_base_background - k_angle * sqrt(delta))) / delta)
        print("   k_speed:", k_speed, "\n   k_diff:", k_diff, "     k_diff*(1-k_forward):", k_diff*(1-k_forward))
        k_diff = k_diff*(1-k_forward)

        speed_primary = base_speed * k_diff * 0.9
        speed_secondary = base_speed / k_diff
        """ red line (17), light background (70)
            if forward sensor at line """
        compare = delta_base_background / 40  # /20  # !!!!!!!!!!
        if delta_lr > compare:
            sr = speed_primary
            sl = speed_secondary
            if base_color > background_color:
                sr = speed_secondary
                sl = speed_primary
            str_turn = "!!!!!!  at right!!"
            if right > left:
                sl = speed_primary
                sr = speed_secondary
                if base_color > background_color:
                    sl = speed_secondary
                    sr = speed_primary
                str_turn = "++++++  at left!!"

            print(str_turn)
        # check overspeed
        if sl > 1:
            sl = 0
            count = 500
        if sr > 1:
            sr = 0
            count = 500
        # set calculated speeds
        drivetrain_control.set_speeds(
            map_values(sl, 0, 1, 0, 120),
            map_values(sr, 0, 1, 0, 120))

        time.sleep(0.015)

    # stop at end of function
    drivetrain_control.set_speeds(
        map_values(0, 0, 1, 0, 120),
        map_values(0, 0, 1, 0, 120))
    return 0


def drive_line(robot, **_):
    drive_color(robot.drivetrain, robot.sensors)


def search_color(drivetrain_control: DriveTrainWrapper, robot_sensors: SensorPortWrapper, line_color, func_search_lr):
    """ searches current line and background colors
    when finished color sensor should be at the center of line (left color == right color)"""
    base_speed = 0.03

    func_search_lr(line_color)
    res = robot_sensors["RGB"].read()
    sensors = [rgb_to_hsv(*_) for _ in struct.iter_unpack("<BBB", res)]
    base_color, background_color, i, colors, colors_grey = detect_line_background_colors(sensors)
    print(colors)

    count = 0
    while count < 20:  # 800:
        count += 1
        # get colors
        res = robot_sensors["RGB"].read()
        sensors = [rgb_to_hsv(*_) for _ in struct.iter_unpack("<BBB", res)]
        base_color_, background_color_, i, colors_grey, colors = detect_line_background_colors(sensors)
        if base_color < background_color:
            base_color = min(base_color_, base_color)
            background_color = max(background_color_, background_color)
        else:
            base_color = max(base_color_, base_color)
            background_color = min(background_color_, background_color)

        forward, left, right, center = colors_grey
        print("   ", base_color, background_color, "___", forward, left, right, center, "i:", i, colors)

        delta_base_background = abs(background_color - base_color)
        delta = delta_base_background * 1.03

        drivetrain_control.set_speeds(
            map_values(base_speed, 0, 1, 0, 120),
            map_values(-base_speed, 0, 1, 0, 120))
        time.sleep(0.02)
    drivetrain_control.set_speeds(
        map_values(0, 0, 1, 0, 120),
        map_values(0, 0, 1, 0, 120))
    time.sleep(0.2)

    count = 0
    while count < 40:  # 800:
        count += 1
        # get colors
        res = robot_sensors["RGB"].read()
        sensors = [rgb_to_hsv(*_) for _ in struct.iter_unpack("<BBB", res)]
        base_color_, background_color_, i, colors_grey, colors = detect_line_background_colors(sensors)
        if base_color < background_color:
            base_color = min(base_color_, base_color)
            background_color = max(background_color_, background_color)
        else:
            base_color = max(base_color_, base_color)
            background_color = min(background_color_, background_color)

        forward, left, right, center = colors_grey
        print("   ", base_color, background_color, "___", forward, left, right, center, "i:", i, colors)

        delta_base_background = abs(background_color - base_color)
        delta = delta_base_background * 1.03

        drivetrain_control.set_speeds(
            map_values(-base_speed, 0, 1, 0, 120),
            map_values(base_speed, 0, 1, 0, 120))
        time.sleep(0.02)
    drivetrain_control.set_speeds(
        map_values(0, 0, 1, 0, 120),
        map_values(0, 0, 1, 0, 120))
    time.sleep(0.2)
    count = 0
    while count < 50:  # 800:
        count += 1
        # get colors
        res = robot_sensors["RGB"].read()
        sensors = [rgb_to_hsv(*_) for _ in struct.iter_unpack("<BBB", res)]
        base_color_, background_color_, i, colors_grey, colors = detect_line_background_colors(sensors)
        if base_color < background_color:
            base_color = min(base_color_, base_color)
            background_color = max(background_color_, background_color)
        else:
            base_color = max(base_color_, base_color)
            background_color = min(background_color_, background_color)

        forward, left, right, center = colors_grey
        print("   ", base_color, background_color, "___", forward, left, right, center, "i:", i, colors)

        delta_base_background = abs(background_color - base_color)
        delta = delta_base_background * 1.03

        if abs(left-right) < 5 and abs(forward-base_color) < 10:
            drivetrain_control.set_speeds(
                map_values(0, 0, 1, 0, 120),
                map_values(0, 0, 1, 0, 120))
            return 1
            # return detected_color_name

        drivetrain_control.set_speeds(
            map_values(base_speed, 0, 1, 0, 120),
            map_values(-base_speed, 0, 1, 0, 120))
        time.sleep(0.02)

    drivetrain_control.set_speeds(
        map_values(0, 0, 1, 0, 120),
        map_values(0, 0, 1, 0, 120))
    time.sleep(0.2)
    return 0
    # return 0 -- color don't detected now


def search_lr(color):
    """this function should search color where we change direction
    when founded we stop current line follower and go to the next step"""
    print("\n!\n", color)


def search_line(robot, func=search_lr, **_):
    """this function is step 2, we search line to follow and return line color and background color
    when function ends the color sensor position is left color == right color"""
    color_line = "red"
    search_color(robot.drivetrain, robot.sensors, color_line, func)

builtin_scripts = {
    'drive_2sticks': drive_2sticks,
    'drive_joystick': drive_joystick,
    'drive_line': drive_line,
    'search_line': search_line,
}

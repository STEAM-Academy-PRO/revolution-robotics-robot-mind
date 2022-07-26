# SPDX-License-Identifier: GPL-3.0-only
import struct
import time

from math import sqrt, sin, cos, pi, atan2

from revvy.scripting.robot_interface import DriveTrainWrapper, SensorPortWrapper
from revvy.utils.functions import map_values


def stick_controller(x, y):
    """Two wheel speeds are controlled independently, just pass through

    >>> stick_controller(0, 0)
    (0, 0)
    >>> stick_controller(0.2, 0.3)
    (0.2, 0.3)
    >>> stick_controller(-0.2, -0.3)
    (-0.2, -0.3)
    """
    return x, y


def joystick(x, y):
    """Calculate control vector length and angle based on touch (x, y) coordinates

    >>> joystick(0, 0)
    (0.0, 0.0)
    >>> joystick(0, 1)
    (1.0, 1.0)
    >>> joystick(0, -1)
    (-1.0, -1.0)
    >>> joystick(1, 0)
    (1.0, -1.0)
    >>> joystick(-1, 0)
    (-1.0, 1.0)
    """

    if x == y == 0:
        return 0.0, 0.0

    angle = atan2(y, x) - pi / 2
    length = sqrt(x * x + y * y)

    v = length * cos(angle)
    w = length * sin(angle)

    sr = round(v + w, 3)
    sl = round(v - w, 3)
    return sl, sr


def get_color_name(r, g, b):
    name = 'not_defined'
    if r < 85 and g < 85 and b < 85:
        name = 'black'
        return name
    if r > 195 and g > 195 and b > 195:
        name = 'white'
        return name
    if r > 120 and g < 120 and b < 120:
        name = 'red'
        return name
    if r < 120 and g > 100 and b < 140:  # b < 120
        name = 'green'
        return name
    if r < 120 and g < 120 and b > 120:
        name = 'blue'
        return name
    if r > 180 and g > 180 and b < 160:
        name = 'yellow'
        return name
    if r < 160 and g > 180 and b > 180:
        name = 'cyan'
        return name
    return name


def rgb_to_hsv_grey(red, green, blue):
    r, g, b = red / 255.0, green / 255.0, blue / 255.0
    grey = 0.299 * red + 0.587 * green + 0.114 * blue
    mx = max(r, g, b)
    mn = min(r, g, b)
    df = mx - mn
    h = 1.0

    if mx == mn:
        h = 0
    elif mx == r:
        h = (60 * ((g - b) / df) + 360) % 360
    elif mx == g:
        h = (60 * ((b - r) / df) + 120) % 360
    elif mx == b:
        h = (60 * ((r - g) / df) + 240) % 360
    if mx == 0:
        s = 0
    else:
        s = (df / mx) * 100
    v = mx * 100
    return round(h, 1), round(s, 1), round(v, 1), round(grey, 1), get_color_name(red, green, blue), (red, green, blue)


def detect_line_background_colors(sensors):
    res = [[], [], []]  # [H] [S] [V]
    grey = []
    name = []
    rgb_val = []
    # print(sensors)
    for sensor in sensors:
        res[0].append(sensor[0])
        res[1].append(sensor[1])
        res[2].append(sensor[2])
        grey.append(sensor[3])
        name.append(sensor[4])
        rgb_val.append(sensor[5])
    # print(res)
    delta = []  # searching of most signed from H S V
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
    background_name = name[grey.index(background)]
    line_name = name[grey.index(line)]

    return line, background, line_name, background_name, i, tuple(grey), tuple(name)


def rotate_for_search(
        drivetrain_control: DriveTrainWrapper,
        robot_sensors: SensorPortWrapper,
        base_color,
        background_color,
        direction: int,
        count_time: int,
        base_speed=0.03,
        stop_line=0,
):
    if direction:
        base_speed = -base_speed
    drivetrain_control.set_speeds(
        map_values(base_speed, 0, 1, 0, 120),
        map_values(-base_speed, 0, 1, 0, 120))
    count = 0
    while count < count_time:
        count += 1
        res = robot_sensors["RGB"].read()
        sensors = [rgb_to_hsv_grey(*_) for _ in struct.iter_unpack("<BBB", res)]
        base_color_, background_color_, line_name_, background_name_, i, colors_grey, colors = \
            detect_line_background_colors(sensors)
        if base_color < background_color:
            base_color = min(base_color_, base_color)
            background_color = max(background_color_, background_color)
        else:
            base_color = max(base_color_, base_color)
            background_color = min(background_color_, background_color)

        forward, left, right, center = colors_grey
        # print("   ", base_color, background_color, "___", forward, left, right, center, "i:", i, colors)
        delta_base_background = abs(background_color - base_color)
        if stop_line:
            if abs(left - right) < 0.08 * (left + right) \
                    and (
                    abs(center - base_color) < 0.3 * delta_base_background
                    or abs(forward - base_color) < 0.3 * delta_base_background
            ):
                drivetrain_control.set_speeds(
                    map_values(0, 0, 1, 0, 120),
                    map_values(0, 0, 1, 0, 120))
                return 1, base_color, background_color, line_name_, background_name_
        time.sleep(0.02)
    drivetrain_control.set_speeds(
        map_values(0, 0, 1, 0, 120),
        map_values(0, 0, 1, 0, 120))
    time.sleep(0.2)
    return 0, base_color, background_color, None, None


def search_line(drivetrain_control: DriveTrainWrapper, robot_sensors: SensorPortWrapper):
    """ searches current line and background colors
    when finished color sensor should be at the center of line (left color == right color)"""
    # robot.drivetrain, robot.sensors

    res = robot_sensors["RGB"].read()
    sensors = [rgb_to_hsv_grey(*_) for _ in struct.iter_unpack("<BBB", res)]
    base_color, background_color, line_name, background_name, i, colors, colors_grey = \
        detect_line_background_colors(sensors)

    status, base_color, background_color, line_color_name, _ = rotate_for_search(drivetrain_control, robot_sensors, base_color,
                                                                    background_color, 0, 40, 0.03, 0)
    status, base_color, background_color, line_color_name, _ = rotate_for_search(drivetrain_control, robot_sensors, base_color,
                                                                    background_color, 1, 120, 0.03, 0)
    status, base_color, background_color, line_color_name, _ = rotate_for_search(drivetrain_control, robot_sensors, base_color,
                                                                    background_color, 0, 160, 0.03, 1)
    return base_color, background_color, line_color_name


def search_lr(colors: tuple, color='', side=''):
    """this function should search color where we change direction
    when founded we stop current line follower and go to the next step"""
    if color == '' or side == '':
        print("color or side aren't sat")
        return False
    forward, left, right, center = colors
    if side is 'left':
        if left == color:
            print(f"\n\nchannel 2 is {color} at {side}\n\n")
            return True
    elif side is 'right':
        if right == color:
            print(f"\n\nchannel 3 is {color} at {side}\n\n")
            return True

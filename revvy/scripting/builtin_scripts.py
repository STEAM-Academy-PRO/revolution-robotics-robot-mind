# SPDX-License-Identifier: GPL-3.0-only
import struct
import time

from math import sqrt

from revvy.scripting.robot_interface import DriveTrainWrapper, SensorPortWrapper
from revvy.scripting.robot_interface import MotorConstants as Motor
from revvy.utils.functions import clip, map_values
from revvy.scripting.controllers import stick_controller, joystick, rgb_to_hsv_grey, detect_line_background_colors,\
    search_line, search_lr


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


def follow_line(
        drivetrain_control: DriveTrainWrapper, robot_sensors: SensorPortWrapper,
        base_color=0, background_color=0, line_name='not_defined', count_time=100, base_speed=0.2,
        func_search_lr=None, desired_color='', side='',
):
    """ need to set correct line and background colors, this colors we need to get from search_color function
    it is function for step 3"""
    if base_color == 0 or background_color == 0 or line_name == 'not_defined':
        print("line_grey:", base_color, "background_grey:", background_color, "line_color_name:", line_name)
        return 2
    count = 0
    k_speed = 1 - 0.23 * base_speed
    if k_speed > 0.99:
        k_speed = 0.99

    while count < count_time:  # 500 800:
        count += 1
        # get colors
        res = robot_sensors["RGB"].read()
        sensors = [rgb_to_hsv_grey(*_) for _ in struct.iter_unpack("<BBB", res)]
        base_color_, background_color_, line_name_, background_name_, i, colors_grey, colors =\
            detect_line_background_colors(sensors)

        forward, left, right, center = colors_grey
        forward_name, left_name, right_name, center_name = colors
        print("   ", base_color, background_color, "___", forward, left, right, center, "___", colors)

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

        # check left/right lines
        if func_search_lr:
            if func_search_lr(colors, desired_color, side):
                drivetrain_control.set_speeds(
                    map_values(0, 0, 1, 0, 120),
                    map_values(0, 0, 1, 0, 120))
                print("stop, line found")
                return 0

        forward_level = 0.35  #  0.40 good for base_speed = 0.2
        k_forward = 0
        temp = abs(forward - base_color) / delta_base_background
        if temp > 0.25:
            k_forward = forward_level * temp
        k_angle = 1.02 + sqrt(delta_base_background / 6.8)  # 7.0 good for base_speed = 0.2
        sl = base_speed
        sr = base_speed
        delta_lr = abs(right - left)
        # print("delta:", round(delta, 2), "    delta_lr:", round(delta_lr, 2),
        #       "    k_angle:", round(k_angle, 3), "    k_forward:", round(k_forward, 3))
        k_diff = (1 - k_speed) \
                 + k_speed * ((k_angle * sqrt(abs(delta - delta_lr)) + (
                    delta_base_background - k_angle * sqrt(delta))) / delta)
        # print("k_speed:", round(k_speed, 3), "    k_diff:", round(k_diff, 3),
        #       "   k_diff*(1-k_forward):", round(k_diff * (1 - k_forward), 3))

        if forward_name == line_name:
            k_forward = 0

        k_diff = k_diff*(1-k_forward)

        speed_primary = base_speed * k_diff  # * 0.9
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
            str_turn = "          >>>>>>>>>>>"
            if right > left:
                sl = speed_primary
                sr = speed_secondary
                if base_color > background_color:
                    sl = speed_secondary
                    sr = speed_primary
                str_turn = "          <<<<<<<<<<<"
            print(str_turn)
        # check overspeed
        if sl > 1:
            sl = 0
            count = count_time
        if sr > 1:
            sr = 0
            count = count_time
        # set calculated speeds
        drivetrain_control.set_speeds(
            map_values(sl, 0, 1, 0, 120),
            map_values(sr, 0, 1, 0, 120))

        time.sleep(0.015)

    # stop at end of function
    drivetrain_control.set_speeds(
        map_values(0, 0, 1, 0, 120),
        map_values(0, 0, 1, 0, 120))
    return 3


# def algorithm(robot, func=search_lr, **_):
def algorithm(robot, **_):
    """this function is step 2, we search line to follow and return line color and background color
    when function ends the color sensor position is left color == right color"""
    line_color = "blue"
    base_color, background_color, line_color_name = search_line(robot.drivetrain, robot.sensors)
    time.sleep(0.4)
    if line_color_name == line_color:
        res = follow_line(robot.drivetrain, robot.sensors, base_color, background_color, line_color, 500, 0.2,
                          search_lr, 'green', 'left')
        time.sleep(0.4)
        if res == 0:
            robot.drive(direction=Motor.DIRECTION_FWD, rotation=0.4, unit_rotation=Motor.UNIT_ROT, speed=25,    # Motor.UNIT_SEC, speed=25,
                        unit_speed=Motor.UNIT_SPEED_RPM)
            time.sleep(0.5)
            robot.turn(direction=Motor.DIRECTION_LEFT, rotation=90, unit_rotation=Motor.UNIT_TURN_ANGLE, speed=25,
                       unit_speed=Motor.UNIT_SPEED_RPM)
            robot.drivetrain.set_speeds(
                map_values(0, 0, 1, 0, 120),
                map_values(0, 0, 1, 0, 120))
    else:
        print(f"there aren't found {line_color} line. it is {line_color_name}")
        res = robot.sensors["RGB"].read()
        sensors = [rgb_to_hsv_grey(*_) for _ in struct.iter_unpack("<BBB", res)]
        print(sensors)
        print(detect_line_background_colors(sensors))
        return 1
    time.sleep(0.4)

    line_color = "green"
    base_color, background_color, line_color_name = search_line(robot.drivetrain, robot.sensors)
    if line_color_name == line_color:
        res = follow_line(robot.drivetrain, robot.sensors, base_color, background_color, line_color, 200, 0.2,
                          search_lr, 'red', 'left')
        time.sleep(0.4)
        if res == 0:
            robot.drive(direction=Motor.DIRECTION_FWD, rotation=0.41, unit_rotation=Motor.UNIT_ROT, speed=25,    # Motor.UNIT_SEC, speed=25,
                        unit_speed=Motor.UNIT_SPEED_RPM)
            time.sleep(0.2)
            robot.turn(direction=Motor.DIRECTION_LEFT, rotation=90, unit_rotation=Motor.UNIT_TURN_ANGLE, speed=25,
                       unit_speed=Motor.UNIT_SPEED_RPM)
            robot.drivetrain.set_speeds(
                map_values(0, 0, 1, 0, 120),
                map_values(0, 0, 1, 0, 120))
    else:
        print(f"there aren't found {line_color} line. it is {line_color_name}")
        res = robot.sensors["RGB"].read()
        sensors = [rgb_to_hsv_grey(*_) for _ in struct.iter_unpack("<BBB", res)]
        print(sensors)
        print(detect_line_background_colors(sensors))
        return 1
    time.sleep(0.4)

    line_color = "red"
    base_color, background_color, line_color_name = \
        search_line(robot.drivetrain, robot.sensors)
    if line_color_name == line_color:
        res = follow_line(robot.drivetrain, robot.sensors, base_color, background_color, line_color, 200, 0.2)
        print(f"search_line done, res: {res}")
    else:
        print(f"there aren't found {line_color} line. it is {line_color_name}")
        res = robot.sensors["RGB"].read()
        sensors = [rgb_to_hsv_grey(*_) for _ in struct.iter_unpack("<BBB", res)]
        print(sensors)
        print(detect_line_background_colors(sensors))
        return 1
    return 0


builtin_scripts = {
    'drive_2sticks': drive_2sticks,
    'drive_joystick': drive_joystick,
    'algorithm': algorithm,
}

import struct
import time

from math import sqrt, sin, cos, pi, atan2

from revvy.scripting.robot_interface import DriveTrainWrapper, SensorPortWrapper


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

from typing import Callable

from revvy.scripting.robot_interface import DriveTrainWrapper, RobotWrapper
from revvy.scripting.robot_interface import MotorConstants as Motor
from revvy.utils.functions import clip, map_values
from revvy.scripting.controllers import stick_controller, joystick


def normalize_analog(b: int) -> float:
    """
    >>> normalize_analog(0)
    -1.0
    >>> normalize_analog(255)
    1.0
    >>> normalize_analog(127)
    0.0
    """
    return clip((b - 127) / 127.0, -1.0, 1.0)


def drive(
    drivetrain_control: DriveTrainWrapper,
    channels,
    controller: Callable[[float, float], tuple[float, float]],
) -> None:
    x = normalize_analog(channels[0])
    y = normalize_analog(channels[1])

    sl, sr = controller(x, y)

    drivetrain_control.set_speeds(map_values(sl, 0, 1, 0, 120), map_values(sr, 0, 1, 0, 120))


def drive_joystick(robot: RobotWrapper, channels, **_):
    drive(robot.drivetrain, channels, joystick)


def drive_2sticks(robot: RobotWrapper, channels, **_):
    drive(robot.drivetrain, channels, stick_controller)


builtin_scripts = {
    "drive_2sticks": drive_2sticks,
    "drive_joystick": drive_joystick,
}

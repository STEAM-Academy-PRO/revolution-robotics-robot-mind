from typing import Callable

from revvy.scripting.robot_interface import DriveTrainWrapper, RobotWrapper
from revvy.scripting.robot_interface import MotorConstants as Motor
from revvy.utils.functions import clip, map_values
from revvy.scripting.controllers import stick_controller, joystick
from revvy.utils.logger import get_logger

log = get_logger("drivetrain")

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

def drive_4sticks(robot: RobotWrapper, channels, **_):
    drive(robot.drivetrain, channels, joystick)

    a = normalize_analog(channels[2])
    b = normalize_analog(channels[3])

    a_speed = map_values(a, 0, 1, 0, 120)
    b_speed = map_values(b, 0, 1, 0, 120)

    log(f"a: {a}, b: {b}")
    log(f"motors: {robot.motors[0]}")

    try:
        robot.motors['motor3'].spin(direction=Motor.DIRECTION_FWD, rotation=a_speed, unit_rotation=Motor.UNIT_SPEED_RPM)
    except Exception as e:
        log(f"Error setting motor speed: motor4 {e}")
        pass
    try:
        robot.motors['motor6'].spin(direction=Motor.DIRECTION_FWD, rotation=b_speed, unit_rotation=Motor.UNIT_SPEED_RPM)
    except Exception as e:
        log(f"Error setting motor speed: motor6 {e}")
        pass

def drive_4sticks_b(robot: RobotWrapper, channels, **_):
    drive(robot.drivetrain, channels, joystick)

    a = normalize_analog(channels[2])
    b = normalize_analog(channels[3])

    a_speed = map_values(a, 0, 1, 0, 120)
    b_speed = map_values(b, 0, 1, 0, 120)

    log(f"a: {a}, b: {b}")
    log(f"motors: {robot.motors[0]}")

    try:
        robot.motors['motor3'].servo(angle=a_speed)
    except Exception as e:
        log(f"Error setting motor speed: motor4 {e}")
        pass
    try:
        robot.motors['motor6'].servo(angle=b_speed)
    except Exception as e:
        log(f"Error setting motor speed: motor6 {e}")
        pass



builtin_scripts = {
    "drive_2sticks": drive_2sticks,
    "drive_4sticks": drive_4sticks,
    "drive_4sticks_b": drive_4sticks_b,
    "drive_joystick": drive_joystick,
}

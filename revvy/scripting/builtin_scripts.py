# SPDX-License-Identifier: GPL-3.0-only
from revvy.robot.ports.sensors.revvy_i2c import Color
from revvy.scripting.robot_interface import DriveTrainWrapper
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


prev_pos = 0
integrator = 0


def drive_linefollower_demo(robot, channels, **_):

    k_p = -0.0013
    k_i = 0.0001
    k_d = -0.001

    follow_color = Color.WHITE

    line = robot.sensors[1].read()

    fwd_speed = normalize_analog(channels[1])
    turn_speed = normalize_analog(channels[0])

    global prev_pos, integrator

    if line.color == follow_color:
        line_position = line.line_pos  # negative means we have to turn left (left sensor is on line)
        # fwd_speed *= map_values(clip(line_position, 0, 100), 0, 100, 1, 0.25)
        integrator = clip(integrator + line_position, -100, 100)
        cur_spd = fwd_speed

    else:
        line_position = (-75 if prev_pos < 0 else 75)
        cur_spd = fwd_speed / 3
        integrator = 0

    if abs(turn_speed) < 0.25:

        turn_speed = k_p * line_position + k_i * integrator + k_d * (line_position - prev_pos)

        sl = cur_spd + turn_speed
        sr = cur_spd - turn_speed

        robot.drivetrain.set_speeds(
            map_values(sl, 0, 1, 0, 75),
            map_values(sr, 0, 1, 0, 75))
    else:
        prev_pos = line.line_pos
        integrator = 0
        drive_joystick(robot, channels)

    prev_pos = line_position


builtin_scripts = {
    'drive_2sticks': drive_2sticks,
    'drive_joystick': drive_linefollower_demo
}

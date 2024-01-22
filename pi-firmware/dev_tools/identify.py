#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-only

# motor identification script, used in conjunction with rtt-viewer. it drives a motor with
# specific power values, and the speed is measured by rtt-viewer. the data can be used to tune
# the motor model parameters for the control loops, or just to see differences between individual
# motors.

import time

from revvy.robot.configurations import Motors
from revvy.utils.thread_wrapper import periodic
from revvy.robot.robot import Robot

if __name__ == "__main__":
    with Robot() as robot:
        robot.reset()
        status_update_thread = periodic(robot.update_status, 0.02, "RobotStatusUpdaterThread")
        status_update_thread.start()

        motor = robot.motors[4]
        motor.configure(Motors.RevvyMotor)

        training = False
        if training:
            pwms = [1, 6, 7, 8, 9, 10, 30, 50, 70, 100]
        else:
            pwms = range(0, 101, 5)

        for pwm in pwms:
            motor.set_power(pwm)
            time.sleep(2)
            motor.set_power(0)
            time.sleep(1)

        status_update_thread.exit()

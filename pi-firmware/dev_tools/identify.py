#!/usr/bin/python3

# motor identification script. it drives a motor with specific power values, and reads the speed.
# the data can be used to tune the motor model parameters for the control loops, or just to see
# differences between individual motors.

import time
import sys

from revvy.hardware_dependent.rrrc_transport_i2c import RevvyTransportI2C
from revvy.robot.configurations import Motors
from revvy.utils.thread_wrapper import periodic
from revvy.robot.robot import Robot
from revvy.robot.ports.common import PortInstance
from revvy.robot.ports.motors.dc_motor import DcMotorController
from revvy.robot_manager import RevvyStatusCode
from revvy.firmware_updater import update_firmware_if_needed

if __name__ == "__main__":
    interface = RevvyTransportI2C(bus=1)

    ### Before we enter the main loop, let's load up
    if not update_firmware_if_needed(interface):
        # exiting with integrity error forces the loader to try a previous package
        sys.exit(RevvyStatusCode.INTEGRITY_ERROR)

    robot = Robot(interface)

    robot.reset()
    status_update_thread = periodic(robot.update_status, 0.02, "RobotStatusUpdaterThread")
    status_update_thread.start()

    motor = robot.motors[4]
    motor.configure(Motors.EmulatedRevvyMotor)

    # collect (input, speed) pairs
    recorded_pwms = []
    recorded_speeds = []

    def _on_motor_status_changed(port: PortInstance[DcMotorController]) -> None:
        recorded_pwms.append(port.driver.power)
        recorded_speeds.append(port.driver.speed)
        print(f"power: {port.driver.power}, speed: {port.driver.speed}")

    motor.driver.on_status_changed.add(_on_motor_status_changed)

    training = False
    if training:
        pwms = [1, 6, 7, 8, 9, 10, 30, 50, 70, 100]
    else:
        pwms = range(0, 101, 5)

    for pwm in pwms:
        motor.driver.set_power(pwm)
        time.sleep(2)
        motor.driver.set_power(0)
        time.sleep(1)

    status_update_thread.exit()

    # save data as csv
    with open("motor_data.csv", "w") as f:
        f.write("power,speed\n")
        for i in range(len(recorded_pwms)):
            f.write(f"{recorded_pwms[i]},{recorded_speeds[i]}\n")

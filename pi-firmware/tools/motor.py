#!/usr/bin/python3

from revvy.robot.configurations import Motors
from revvy.utils.thread_wrapper import periodic
from revvy.robot.robot import Robot

if __name__ == "__main__":
    with Robot() as robot:

        def update():
            robot.update_status()

        robot.reset()
        status_update_thread = periodic(update, 0.02, "RobotStatusUpdaterThread")
        status_update_thread.start()

        for idx in range(1, 7):
            robot.motors[idx].configure(Motors.RevvyMotor)
            robot.motors[idx].on_status_changed.add(lambda p, i=idx: print(i, p.speed, p.pos))

        print("Press Enter to stop")
        input()
        status_update_thread.exit()

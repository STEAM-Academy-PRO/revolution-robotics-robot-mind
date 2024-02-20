#!/usr/bin/python3

import time
from revvy.utils.progress_indicator import ProgressIndicator
from revvy.utils.thread_wrapper import periodic
from revvy.robot.robot import Robot

if __name__ == "__main__":
    with Robot() as robot:

        def update():
            robot.update_status()

        robot.reset()
        status_update_thread = periodic(update, 0.02, "RobotStatusUpdaterThread")
        status_update_thread.start()

        progress = ProgressIndicator(robot.led, 100, 0x00FF00, 0xFF00FF)
        while True:
            for i in range(101):
                progress.update(i)
                time.sleep(0.1)

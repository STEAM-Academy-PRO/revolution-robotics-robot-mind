""" MJPG Streamer to stream connected webcam to web interface """

import threading
import subprocess
import time
from typing import Callable
from revvy.robot.robot_events import RobotEvent

from revvy.utils.logger import LogLevel, get_logger

log = get_logger("Camera")

STREAMER_FOLDER = "/home/pi/mjpg-streamer/mjpg-streamer-experimental/"
STREAMER_COMMAND = 'mjpg_streamer -o "output_http.so -w ./www" -i "input_uvc.so -r 1280x960 -f 30"'


class Camera:
    def __init__(self, trigger: Callable) -> None:
        self._trigger = trigger
        self._process = None
        self.stop()

    def start(self) -> None:
        # Create a new thread that runs the function defined above
        self._thread = threading.Thread(target=self._run_bash_camera_script)

        self._thread.daemon = (
            True  # Allows the thread to be automatically killed when the main program exits
        )
        self._thread.start()

        log("Camera stream starting")

    def stop(self) -> None:
        self._stop()
        self._trigger(RobotEvent.CAMERA_STOPPED)

    def _stop(self) -> None:
        try:
            kill_process = subprocess.Popen(["killall", "mjpg_streamer"])
            kill_process.wait()
        except Exception:
            pass

    def _run_bash_camera_script(self) -> None:

        log(STREAMER_COMMAND)

        self._stop()

        # Seems to reset the interface and fix "not found" errors
        modprobe = subprocess.Popen(["/usr/sbin/modprobe", "bcm2835-v4l2"])
        modprobe.wait()

        self._process = subprocess.Popen(
            STREAMER_COMMAND,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            shell=True,
            cwd=STREAMER_FOLDER,
        )

        assert self._process.stdout is not None

        # Continuously read and print the output
        while True:
            output_line = self._process.stdout.readline()

            log(output_line.strip())

            # Check if the process has terminated.
            if self._process.poll() is not None:
                # The process has terminated; check if it was due to an error.

                if self._process.returncode != 0:
                    self._trigger(RobotEvent.CAMERA_STOPPED)

                    log(self._process.stdout.read(), LogLevel.ERROR)

                    if "No such file or directory" in output_line:
                        self._trigger(RobotEvent.CAMERA_ERROR, "Camera not found")
                    else:
                        self._trigger(RobotEvent.CAMERA_ERROR, output_line)

                    log(
                        f"Camera process terminated with error. Return code: {self._process.returncode}"
                    )
                    return
                break  # Exit the loop and don't attempt to restart the process.

            if output_line:
                if "enabled" in output_line:  # Camera stream started
                    time.sleep(2)
                    self._trigger(RobotEvent.CAMERA_STARTED)
                    log("Camera stream started")

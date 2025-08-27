""" MJPG Streamer to stream connected webcam to web interface """

import threading
import subprocess
import time
from typing import Callable
from revvy.robot.robot_events import RobotEvent

from revvy.utils.logger import LogLevel, get_logger

log = get_logger("Camera")

# Installation instructions: camera.md
RESOLUTION_VGA="640x480"
RESOLUTION_LOW="320x240"
FPS_HIGH="30"
FPS_LOW="15"

STREAMER_FOLDER = "/home/pi/mjpg-streamer/mjpg-streamer-experimental/"
STREAMER_COMMAND = 'mjpg_streamer -o "output_http.so -w ./www"'


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

    def list_devices(self):
        try:
            # run with check=False so non-zero exit codes won't raise exceptions
            result = subprocess.run(
                ["v4l2-ctl", "--list-devices"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                check=False
            )
            return result.stdout.strip()
        except FileNotFoundError:
            return "v4l2-ctl not found. Please install v4l-utils."

    def find_webcam_device(self) -> None:

        # Get the latest device that is a webcam
        device_list = self.list_devices()
        device_list = [line.strip() for line in device_list.split('\n') if 'video' in line]
        if not device_list:
            log('No webcam found')
            return None
        return device_list[0]

    def _run_bash_camera_script(self) -> None:

        # Get the latest device that is a webcam
        device = self.find_webcam_device()

        CURRENT_STREAMER_COMMAND = f'{STREAMER_COMMAND} -i "input_uvc.so --device {device} -r {RESOLUTION_LOW} -f {FPS_LOW}"'

        log(CURRENT_STREAMER_COMMAND)

        self._stop()

        # Seems to reset the interface and fix "not found" errors
        modprobe = subprocess.Popen(["/usr/sbin/modprobe", "bcm2835-v4l2"])
        modprobe.wait()

        self._process = subprocess.Popen(
            CURRENT_STREAMER_COMMAND,
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

"""
Store and DEBOUNCE robot events to higher layers.

This class is supposed to store all the robot related states
and send notifications if something changes about it.

It polls the MCU for updates in any states.

"""

from functools import partial
from math import floor
import math
import traceback
from revvy.mcu.rrrc_transport import TransportException
from revvy.robot.remote_controller import RemoteController

from revvy.robot.robot_events import RobotEvent
from revvy.utils.emitter import Emitter
from revvy.utils.logger import LogLevel, get_logger
from revvy.utils.observable import Observable
from revvy.utils.thread_wrapper import ThreadWrapper, periodic

from typing import TYPE_CHECKING

# To have types, use this to avoid circular dependencies.
if TYPE_CHECKING:
    from revvy.robot.robot import Robot

log = get_logger('RobotStatePoller')

class RobotState(Emitter[RobotEvent]):
    """ Sustain a consistent event driven state of the robot """

    def __init__(self, robot: 'Robot', remote_controller: RemoteController):
        self._robot = robot
        self._remote_controller = remote_controller
        self._status_update_thread:ThreadWrapper = None

        # Battery updates: every 2 seconds is enough, if it's unplugged, it's
        # soon enough to notify.
        self._battery = Observable([0]*4, 2)

        self._gyro = Observable([0]*3, throttle_interval=0.1)
        self._orientation = Observable([0]*3, throttle_interval=0.1)

        self._script_variables = Observable ([None]*4, throttle_interval=0.1)

        self._background_control_state = Observable('', throttle_interval=0.1)
        self._timer = Observable(0, throttle_interval=1)

    def start_polling_mcu(self):
        """ Starts a new thread that runs every 5ms to check on MCU status. """
        self._status_update_thread = periodic(self._update, 0.005, "RobotStatusUpdaterThread")

        self._battery.subscribe(partial(self.trigger, RobotEvent.BATTERY_CHANGE))
        self._gyro.subscribe(partial(self.trigger, RobotEvent.GYRO_CHANGE))
        self._orientation.subscribe(partial(self.trigger, RobotEvent.ORIENTATION_CHANGE))
        self._script_variables.subscribe(partial(self.trigger, RobotEvent.BATTERY_CHANGE))

        self._background_control_state.subscribe(partial(self.trigger, RobotEvent.BACKGROUND_CONTROL_STATE_CHANGE))
        self._timer.subscribe(partial(self.trigger, RobotEvent.TIMER_TICK))

        self._robot.reset()

        self._status_update_thread.start()


    def stop_polling_mcu(self):
        """ Exits the thread. """
        self._status_update_thread.exit()

    def _update(self):
        """
            This runs every 5ms and reads out the robot's statuses.
        """
        # noinspection PyBroadException
        try:
            self._robot.update_status()

            self._battery.set([
                self._robot.battery.main,
                self._robot.battery.chargerStatus,
                self._robot.battery.motor,
                self._robot.battery.motor_battery_present
            ])

            # TODO: Check what this does, and WHY?
            # self._remote_controller.timer_increment()

            # Rotation has pretty high noise. To filter it out, I am cutting off the
            # number's values below 1. `floor` works not to the need of this, and would
            # return -1 for 0.99. Instead, I created a floor, that does the trick and
            # drops the small absolute value of the number properly below 0
            self._gyro.set([
                floor0(getattr(self._robot.imu.rotation, 'x')),
                floor0(getattr(self._robot.imu.rotation, 'y')),
                floor0(getattr(self._robot.imu.rotation, 'z'))
            ])

            ### This seems to do NOTHING.
            self._orientation = ([
                getattr(self._robot.imu.orientation, 'pitch'),
                getattr(self._robot.imu.orientation, 'roll'),
                getattr(self._robot.imu.orientation, 'yaw'),
            ])

            self._script_variables.set(self._robot.script_variables)
            self._background_control_state.set(self._remote_controller.background_control_state)

            # TODO: WHY is this necessary???
            #self._robot_interface.update_timer(self._remote_controller.processing_time)

            # self.process_run_in_bg_requests()
            # self.process_autonomous_requests()

        except TransportException:
            # TODO: This caused the whole app to quit. Why? What is this error?
            log(traceback.format_exc(), LogLevel.ERROR)
            self.trigger(RobotEvent.FATAL_ERROR)
        except BrokenPipeError:
            log("Status Update Error from MCU", LogLevel.WARNING)
        except OSError as e:
            log(f"{str(e)}", LogLevel.WARNING)
        except Exception:
            log(traceback.format_exc())


def floor0(number):
    if number < 0:
        return math.ceil(number)
    else:
        return math.floor(number)
"""
Store and DEBOUNCE robot events to higher layers.

This class is supposed to store all the robot related states
and send notifications if something changes about it.

It polls the MCU for updates in any states.

"""

import traceback
from revvy.bluetooth.data_types import BackgroundControlState, GyroData, ScriptVariables, TimerData
from revvy.mcu.rrrc_transport import TransportException
from revvy.robot.remote_controller import RemoteController

from revvy.robot.robot_events import RobotEvent
from revvy.robot.filters.battery import BatteryState
from revvy.utils.emitter import Emitter
from revvy.utils.logger import LogLevel, get_logger
from revvy.utils.observable import Observable
from revvy.utils.thread_wrapper import ThreadWrapper, periodic
from revvy.utils import error_reporter

from typing import TYPE_CHECKING, Optional

# To have types, use this to avoid circular dependencies.
if TYPE_CHECKING:
    from revvy.robot.robot import Robot

log = get_logger("RobotStatePoller")


class RobotStatePoller(Emitter[RobotEvent]):
    """Maintain a consistent event driven state of the robot"""

    def __init__(self, robot: "Robot", remote_controller: RemoteController):
        super().__init__()
        self._robot = robot
        self._remote_controller = remote_controller
        self._status_update_thread: Optional[ThreadWrapper] = None

        self._battery = BatteryState(throttle_interval=2)
        self._orientation = Observable(GyroData(0, 0, 0), throttle_interval=0.2)
        self._script_variables = Observable(ScriptVariables([None] * 4), throttle_interval=0.1)
        self._background_control_state = Observable(
            BackgroundControlState.STOPPED, throttle_interval=0.1
        )
        self._timer = Observable(TimerData(0), throttle_interval=1)

    def start_polling_mcu(self) -> None:
        """Starts a new thread that runs every 5ms to check on MCU status."""
        self._status_update_thread = periodic(self._update, 0.005, "RobotStatusUpdaterThread")

        self._battery.subscribe(lambda data: self.trigger(RobotEvent.BATTERY_CHANGE, data))
        self._orientation.subscribe(lambda data: self.trigger(RobotEvent.ORIENTATION_CHANGE, data))
        self._script_variables.subscribe(
            lambda data: self.trigger(RobotEvent.SCRIPT_VARIABLE_CHANGE, data)
        )
        self._background_control_state.subscribe(
            lambda data: self.trigger(RobotEvent.BACKGROUND_CONTROL_STATE_CHANGE, data)
        )
        self._timer.subscribe(lambda data: self.trigger(RobotEvent.TIMER_TICK, data))

        self._robot.reset()

        self._status_update_thread.start()

    def stop_polling_mcu(self) -> None:
        """Exits the thread."""
        if self._status_update_thread:
            self._status_update_thread.exit()

    def _update(self) -> None:
        """
        This runs every 5ms and reads out the robot's statuses.
        """
        try:
            self._robot.update_status()

            self._battery.set(self._robot.battery)

            # Send back the timer to the mobile.
            self._remote_controller.timer_increment()
            self._timer.set(self._remote_controller.processing_time)

            self._orientation.set(
                GyroData(
                    self._robot.imu.orientation.pitch,
                    self._robot.imu.orientation.roll,
                    self._robot.imu.orientation.yaw,
                )
            )

            self._script_variables.set(self._robot.script_variables.values())
            self._background_control_state.set(self._remote_controller.background_control_state)

            # This is TEMPORARY and should not be here. Nothing should know about the MCU
            # communication ticks.
            self.trigger(RobotEvent.MCU_TICK)

        except TransportException as e:
            # On MCU communication errors, die.
            log(f"{str(e)}", LogLevel.ERROR)
            log(traceback.format_exc(), LogLevel.ERROR)
            self.trigger(RobotEvent.FATAL_ERROR)
        except BrokenPipeError:
            log("Status Update Error from MCU", LogLevel.WARNING)
        except OSError as e:
            log(f"{str(e)}", LogLevel.WARNING)
        except ValueError:
            # already logged to terminal
            error_reporter.revvy_error_handler.report_error(
                error_reporter.RobotErrorType.SYSTEM, traceback.format_exc()
            )
        except Exception:
            log(traceback.format_exc())

""" Battery status debouncer. """

from revvy.utils.logger import get_logger
from revvy.utils.observable import Observable, SmoothingObservable, simple_average
from revvy.robot.robot import BatteryStatus

log = get_logger("BatteryState")


class BatteryState(Observable[BatteryStatus]):
    """Manage and smoothen battery state level values"""

    def __init__(self, throttle_interval: float):
        # The MCU reads battery every 100ms. Though the MCU provides us a filtered
        # value, it may still be noisy when close to whole % values.
        # To smoothen that out, we take the last 25 values (~2.5sec), and take the minimum.
        self._main = SmoothingObservable(
            0,
            window_size=25,
            throttle_interval=5,
            smoothening_function=lambda history: round(min(history)),
        )
        self._charger_status = Observable(0, throttle_interval=2.0)
        self._motor = SmoothingObservable(0, simple_average, window_size=50, throttle_interval=1.0)

        # The MCU is supposed to send indication. It has code that detect batteries under 4V as not plugged in.
        # This is a reasonable assumption, the minimum battery pack voltage (0%) is set to 5.4V.
        # We just can't say if the pack is really not plugged in vs not all 6 batteries are inserted vs
        # the batteries are just reeeeally flat.
        self._motor_battery_present = Observable(0, throttle_interval=2)

        # Initial state
        initial = BatteryStatus(
            self._charger_status.get(),
            self._motor_battery_present.get(),
            self._main.get(),
            self._motor.get(),
        )

        super().__init__(initial, throttle_interval)

    def set(self, new_data: BatteryStatus):
        self._main.set(new_data.main)
        self._charger_status.set(new_data.chargerStatus)
        self._motor.set(new_data.motor)
        self._motor_battery_present.set(new_data.motor_battery_present)
        super().set(
            BatteryStatus(
                self._charger_status.get(),
                self._motor_battery_present.get(),
                self._main.get(),
                self._motor.get(),
            )
        )

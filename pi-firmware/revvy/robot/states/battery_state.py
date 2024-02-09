""" Battery status debouncer. """

from revvy.mcu.commands import BatteryStatus
from revvy.utils.observable import Observable, SmoothingObservable


class BatteryState(Observable):
    """ Manage and smoothen battery state level values """
    def __init__(self, throttle_interval):
        super().__init__(throttle_interval)
        # Battery gets checked every 5ms and it reads out a DAC value, which has plenty of noise.
        # To smoothen that out, here is a 10000 sized min calculator, meaning: takes every 5ms measurement,
        # puts it in an array, gets the min value, rounds it to disable flickering between values.
        self._main = SmoothingObservable(0, window_size=10000, throttle_interval=5,
                                         smoothening_function=lambda history: round(min(history)))
        self._charger_status = Observable(0, throttle_interval=2)
        self._motor = SmoothingObservable(0, window_size=50, throttle_interval=1)

        # If I understood it correctly, we can not really detect this, only
        # the motor voltage. Why are we having this then???
        self._motor_battery_present = Observable(0, throttle_interval=2)

    def set(self, new_data: BatteryStatus):
        self._main.set(new_data.main)
        self._charger_status.set(new_data.chargerStatus)
        self._motor.set(new_data.motor)
        self._motor_battery_present.set(new_data.motor_battery_present)
        super().set(BatteryStatus(self._charger_status.get(),
                        self._motor_battery_present.get(),
                        self._main.get(),
                        self._motor.get(),
        ))


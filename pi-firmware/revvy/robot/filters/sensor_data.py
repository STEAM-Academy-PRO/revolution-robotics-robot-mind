""" Sensor value wrapper: manages throttling of sensor readings for the mobile app """

from abc import abstractmethod
from typing import Callable, Generic, TypeVar
from revvy.robot.ports.common import PortDriver, PortInstance
from revvy.robot.ports.sensors.simple import BumperSwitch, ColorSensor, ColorSensorReading, Hcsr04
from revvy.utils.logger import get_logger
from revvy.utils.observable import Observable, SmoothingObservable, simple_average
from revvy.robot.ports.sensors.simple import (
    ColorSensorReading,
)

# Sensor does send some noise up, seems to be not working above
# around two meters, but let's be optimistic here.
MAX_ULTRASONIC_SENSOR_DISTANCE = 700  # cm

log = get_logger("sensor states")


Driver = TypeVar("Driver", bound=PortDriver)


class SensorDataFilter(Generic[Driver]):
    def __init__(self, on_data_update: Callable, value: Observable):
        self._value = value
        self._value.subscribe(on_data_update)

    @abstractmethod
    def update(self, port: PortInstance[Driver]): ...


class ColorSensorDataFilter(SensorDataFilter[ColorSensor]):
    """Color sensor value filter"""

    def __init__(self, data_update_callback: Callable):
        super().__init__(
            data_update_callback,
            Observable[ColorSensorReading](ColorSensorReading(b"\x00" * 12), throttle_interval=0.2),
        )

    def update(self, port: PortInstance[ColorSensor]):
        self._value.set(port.driver.value)


class UltrasonicSensorDataFilter(SensorDataFilter[Hcsr04]):
    """Ultrasonic value filter"""

    def __init__(self, data_update_callback: Callable):
        super().__init__(
            data_update_callback,
            SmoothingObservable(
                value=0,
                window_size=3,
                # Do not update more frequent than 200ms
                throttle_interval=0.2,
                smoothening_function=simple_average,
            ),
        )

    def update(self, port: PortInstance[Hcsr04]):
        if port.driver.value is not None and 0 < port.driver.value < MAX_ULTRASONIC_SENSOR_DISTANCE:
            self._value.set(port.driver.value)


class ButtonSensorDataFilter(SensorDataFilter[BumperSwitch]):
    """Button value filter"""

    def __init__(self, data_update_callback: Callable):
        super().__init__(
            data_update_callback,
            SmoothingObservable(
                value=False,
                window_size=3,
                # Do not update more frequent than 200ms
                throttle_interval=0.2,
                # Simple majority vote of the last 3 values
                smoothening_function=lambda last_values: sum(last_values) >= 2,
            ),
        )

    def update(self, port: PortInstance[BumperSwitch]):
        self._value.set(port.driver.value)

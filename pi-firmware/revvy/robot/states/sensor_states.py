""" Sensor value wrapper: manages throttling of sensor readings for the mobile app """

from typing import Callable, Optional
from revvy.robot.configurations import Sensors
from revvy.robot.ports.common import PortInstance
from revvy.robot.ports.sensors.base import SensorPortHandler
from revvy.robot.robot_events import ButtonSensorEvent, DistanceSensorEvent
from revvy.utils.logger import get_logger
from revvy.utils.observable import SmoothingObservable
from revvy.utils.subscription import Disposable

# Sensor does send some noise up, seems to be not working above
# around two meters, but let's be optimistic here.
MAX_ULTRASONIC_SENSOR_DISTANCE = 700  # cm

log = get_logger("sensor states")


def create_sensor_data_wrapper(
    sensor_port: PortInstance, sensor: SensorPortHandler, on_data_update: Callable
) -> Optional[Disposable]:
    """
    Create wrappers that convert raw sensor value into a more
    directly usable one. This is a temporary solution to the problem.
    """

    # Currently our sensors send up pretty much RAW data from the MCU
    # which is ok, but unfortunately that code is all around the place too,
    # so for the time being I create an extra data layer over the sensor
    # port readings to debounce/throttle the surfacing values and not read
    # trash.
    #
    # Ideally, we'll dig down into the bottoms of the drivers and clean the
    # data there and only surface it when it's actually good and reliable.
    # Until now, here is a wrapper.

    if sensor is Sensors.Ultrasonic:
        log(f"ultrasonic on port {sensor_port.id}!")
        return UltrasonicSensorDataHandler(sensor_port, on_data_update)

    elif sensor is Sensors.BumperSwitch:
        log(f"button {sensor_port.id}!")
        return ButtonSensorDataHandler(sensor_port, on_data_update)

    log(f"Sensor is not among the known ones. {str(sensor)}")


class UltrasonicSensorDataHandler(Disposable):
    """Ultrasonic value handler"""

    def __init__(self, sensor_port: PortInstance, on_data_update: Callable):
        self._on_data_update = on_data_update
        self._sensor_port = sensor_port

        sensor_port.driver.on_status_changed.add(self.update)

        self._value = SmoothingObservable(
            value=0,
            window_size=3,
            # Do not update more frequent than 200ms
            throttle_interval=0.2,
            smoothening_function=lambda last_values: sum(last_values) / len(last_values),
        )
        # self._value.subscribe(lambda v: log(f'ultrasonic {v}'))

        self._value.subscribe(self.notify)

    def notify(self, value):
        """Sends DistanceSensorEvent"""
        self._on_data_update(DistanceSensorEvent(self._sensor_port.id, value))

    def update(self, port: PortInstance):
        value = port.driver.value
        # log(f'ultrasonic sensor value {value}')
        if value is not None:
            if 0 < value < MAX_ULTRASONIC_SENSOR_DISTANCE:
                self._value.set(value)

    def dispose(self):
        self._value.unsubscribe(self.notify)


class ButtonSensorDataHandler(Disposable):
    """Button value handler"""

    def __init__(self, sensor_port: PortInstance, on_data_update):
        self._on_data_update = on_data_update
        self._sensor_port_id = sensor_port.id
        sensor_port.driver.on_status_changed.add(self.update)
        self._value = SmoothingObservable(
            value=0,
            window_size=3,
            # Do not update more frequent than 200ms
            throttle_interval=0.2,
            smoothening_function=lambda last_values:
            # Simple last 3 window debounce.
            sum(last_values) / 2 > 0.5,
        )
        self._value.subscribe(self.notify)

    def notify(self, value: bool):
        """Sends ButtonSensorEvent"""
        self._on_data_update(ButtonSensorEvent(port_id=self._sensor_port_id, value=value))

    def update(self, port: PortInstance):
        """dig out the first bit"""
        self._value.set(port.driver.raw_value[0])

    def dispose(self):
        self._value.unsubscribe(self.notify)

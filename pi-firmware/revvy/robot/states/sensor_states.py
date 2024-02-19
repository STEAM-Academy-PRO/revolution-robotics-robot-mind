""" Sensor value wrapper: manages throttling of sensor readings for the mobile app """

from typing import Optional
from revvy.bluetooth.data_types import SensorData
from revvy.robot.configurations import Sensors
from revvy.robot.ports.common import PortInstance
from revvy.robot.ports.sensors.simple import BumperSwitch, Hcsr04
from revvy.robot.robot_events import SensorEventData
from revvy.utils.logger import get_logger
from revvy.utils.observable import SmoothingObservable, simple_average
from revvy.utils.subscription import Disposable

# Sensor does send some noise up, seems to be not working above
# around two meters, but let's be optimistic here.
MAX_ULTRASONIC_SENSOR_DISTANCE = 700  # cm

log = get_logger("sensor states")


def create_sensor_data_wrapper(
    sensor_port: PortInstance, sensor, on_data_update
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

    def __init__(self, sensor_port: PortInstance[Hcsr04], on_data_update):
        self._on_data_update = on_data_update
        self._sensor_port = sensor_port

        sensor_port.driver.on_status_changed.add(self.update)

        self._value = SmoothingObservable(
            value=0,
            window_size=3,
            # Do not update more frequent than 200ms
            throttle_interval=0.2,
            smoothening_function=simple_average,
        )
        # self._value.subscribe(lambda v: log(f'ultrasonic {v}'))

        self._value.subscribe(self.notify)

    def notify(self, value):
        """Need to convert the value back"""

        # This should go down as an int, and the bluetooth should convert
        # it into the byte format data structure.
        byte_array_value = round(value).to_bytes(2, "little") + b"\x00\x00"
        self._on_data_update(SensorEventData(self._sensor_port.id, SensorData(byte_array_value)))

    def update(self, port: PortInstance[Hcsr04]):
        """
        Dig out the first two bites.
        """

        # This layer should NOT contain bit hacking.
        value = int.from_bytes(port.driver.raw_value[0:2], "little")
        # log(f'ultrasonic sensor value {value}')
        if 0 < value < MAX_ULTRASONIC_SENSOR_DISTANCE:
            self._value.set(value)
        # self._value.set(int(port.raw_value))

    def dispose(self):
        self._value.unsubscribe(self.notify)


class ButtonSensorDataHandler(Disposable):
    """Button value handler"""

    def __init__(self, sensor_port: PortInstance[BumperSwitch], on_data_update):
        self._on_data_update = on_data_update
        self._sensor_port_id = sensor_port.id
        sensor_port.driver.on_status_changed.add(self.update)
        self._value = SmoothingObservable(
            value=False,
            window_size=3,
            # Do not update more frequent than 200ms
            throttle_interval=0.2,
            # Simple majority vote of the last 3 values
            smoothening_function=lambda last_values: sum(last_values) >= 2,
        )

        self._value.subscribe(self.on_data_update)

    def on_data_update(self, value):
        """
        We need to convert it back to bits
        to send it back to the bluetooth interface.
        """
        self._on_data_update(
            SensorEventData(SensorData(self._sensor_port_id, b"\x01" if value else b"\x00"))
        )

    def update(self, port: PortInstance[BumperSwitch]):
        """dig out the first bit"""
        self._value.set(port.driver.raw_value[0])

    def dispose(self):
        self._value.unsubscribe(self.on_data_update)

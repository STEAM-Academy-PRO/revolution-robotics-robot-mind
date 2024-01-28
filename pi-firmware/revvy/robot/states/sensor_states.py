from pybleno.hci_socket.Hci import math
from revvy.robot.configurations import Sensors
from revvy.robot.ports.common import PortDriver
from revvy.robot.robot_events import SensorEventData
from revvy.utils.logger import get_logger
from revvy.utils.observable import SmoothingObservable

# Sensor does send some noise up, seems to be not working above
# around two meters, but let's be optimistic here.
MAX_ULTRASONIC_SENSOR_DISTANCE = 300 # cm

log = get_logger('sensor states')

def create_sensor_data_wrapper(sensor_port, sensor, on_data_update):
    """
    Currently our sensors send up pretty much RAW data from the MCU
    which is ok, but unfortunately that code is all around the place too,
    so for the time being I create an extra data layer over the sensor
    port readings to debounce/throttle the surfacing values and not read
    trash.
    Ideally, we'll dig down into the bottoms of the drivers and clean the
    data there and only surface it when it's actually good and reliable.
    Until now, here is a wrapper.
    """
    if sensor is Sensors.Ultrasonic:
        log(f'ultrasonic on port {sensor_port.id}!')
        return UltrasonicSensorDataHandler(sensor_port, on_data_update)

    elif sensor is Sensors.BumperSwitch:
        log(f'button {sensor_port.id}!')
        return ButtonSensorDataHandler(sensor_port, on_data_update)

    log(f'what is this? {str(sensor)}')


class UltrasonicSensorDataHandler:
    """ Ultrasonic value handler """
    def __init__(self, sensor_port: PortDriver, on_data_update):
        self._on_data_update = on_data_update
        self._sensor_port = sensor_port

        sensor_port.on_status_changed.add(self.update)

        self._value = SmoothingObservable(value=0, window_size=5,
                # Do not update more frequent than 200ms
                throttle_interval=0.5,
                smoothening_function=lambda last_values:
                    sum(last_values) / len(last_values)
                )
        self._value.subscribe(lambda v: log(f'ultrasonic {v}'))

        self._value.subscribe(self.notify)

    def notify(self, value):
        """ Need to convert the value back """
        below_100 = round(value % 100)
        hundred = math.floor(value / 100)

        # For 123 creates b'\x23\x01' - which is how we read this back FOR NO GOOD REASON.
        byte_array_value = below_100.to_bytes(1, 'big') + hundred.to_bytes(1, 'big')
        self._on_data_update(
            SensorEventData(self._sensor_port.id, byte_array_value))

    def update(self, port: bytearray):
        """
            Dig out the first two bites.
            I have never seen such an implementation, but seems like
            it reads out two BYTE values, each marking a number from 0-99 for the
            distance data...
        """
        value = int(port.raw_value[0]) + int(port.raw_value[1] * 10)
        # log(f'ultrasonic sensor value {value}')
        if 0 < value < MAX_ULTRASONIC_SENSOR_DISTANCE:
            self._value.set(value)
        # self._value.set(int(port.raw_value))



class ButtonSensorDataHandler:
    """ Button value handler """
    def __init__(self, sensor_port, on_data_update):
        sensor_port.on_status_changed.add(self.update)
        self._value = SmoothingObservable(value=0, window_size=3,
                # Do not update more frequent than 200ms
                throttle_interval=0.2,
                smoothening_function=lambda last_values:
                    # Simple last 3 window debounce.
                    sum(last_values) / 2 > 0.5
                )
        # Debug
        self._value.subscribe(lambda v: log(f'btn {v}'))

        # This is tedious, but we need to convert it back to bits.
        self._value.subscribe(lambda v: on_data_update(
            SensorEventData(sensor_port.id, b'\x01' if v else b'\x00')))

    def update(self, port: bytearray):
        """ dig out the first bit """
        self._value.set(port.raw_value[0])

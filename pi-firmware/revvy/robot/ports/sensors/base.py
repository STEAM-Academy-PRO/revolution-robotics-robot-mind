from abc import abstractmethod
from revvy.robot.ports.common import PortDriver, PortInstance
from revvy.mcu.rrrc_control import RevvyControl
from revvy.robot.ports.common import PortHandler


class SensorPortDriver(PortDriver):
    def __init__(self, port: PortInstance, driver_name: str):
        super().__init__(port, driver_name)
        self._port = port
        self._value = None
        self._raw_value = None

    def on_port_type_set(self):
        pass

    @property
    def has_data(self):
        return self._value is not None

    def update_status(self, data):
        if len(data) == 0:
            self._value = None
            return

        if self._raw_value == data:
            return

        self._raw_value = data
        converted = self.convert_sensor_value(data)

        self._raw_value = data
        if converted is not None:
            self._value = converted

        self.on_status_changed(self._port)

    @property
    def value(self):
        return self._value

    @property
    def raw_value(self):
        return self._raw_value

    @abstractmethod
    def convert_sensor_value(self, raw): raise NotImplementedError


class SensorPortHandler(PortHandler[SensorPortDriver]):
    def __init__(self, interface: RevvyControl):
        port_amount = interface.get_sensor_port_amount()
        port_types = interface.get_sensor_port_types()

        super().__init__("Sensor", interface, NullSensor, port_amount, port_types, interface.set_sensor_port_type)


class NullSensor(SensorPortDriver):
    def __init__(self, port: PortInstance):
        super().__init__(port, 'NotConfigured')

    def update_status(self, data):
        pass

    def convert_sensor_value(self, raw):
        pass

    @property
    def value(self):
        return 0

    @property
    def raw_value(self):
        return 0

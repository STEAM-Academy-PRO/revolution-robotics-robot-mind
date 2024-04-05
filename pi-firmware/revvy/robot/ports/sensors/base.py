from abc import abstractmethod
from revvy.robot.ports.common import DriverConfig, PortDriver, PortInstance
from revvy.mcu.rrrc_control import RevvyControl
from revvy.robot.ports.common import PortHandler


class SensorPortDriver(PortDriver):
    def __init__(self, port: PortInstance["SensorPortDriver"], driver_name: str):
        super().__init__(port, driver_name, "Sensor")
        self._port = port
        self._value = None
        self._raw_value = bytes()

        sensor_port_type = port._supported[driver_name]

        port.interface.set_sensor_port_type(port.id, sensor_port_type)

    @property
    def has_data(self) -> bool:
        return self._value is not None

    def update_status(self, data: bytes):
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

        self.on_status_changed.trigger(self._port)

    @property
    def value(self):
        return self._value

    @property
    def raw_value(self) -> bytes:
        return self._raw_value

    @abstractmethod
    def convert_sensor_value(self, raw: bytes):
        raise NotImplementedError


class SensorPortHandler(PortHandler[SensorPortDriver]):
    def __init__(self, interface: RevvyControl):
        port_amount = interface.get_sensor_port_amount()
        port_types = interface.get_sensor_port_types()

        super().__init__(
            "Sensor",
            interface,
            DriverConfig(driver=NullSensor, config={}),
            port_amount,
            port_types,
            interface.set_sensor_port_type,
        )


class NullSensor(SensorPortDriver):
    def __init__(self, port: PortInstance, config):
        super().__init__(port, "NotConfigured")

    def update_status(self, data: bytes):
        pass

    def convert_sensor_value(self, raw: bytes):
        pass

    @property
    def value(self):
        return 0

    @property
    def raw_value(self) -> bytes:
        return bytes()

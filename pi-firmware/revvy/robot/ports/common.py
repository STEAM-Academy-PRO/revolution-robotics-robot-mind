from abc import ABC, abstractmethod

from revvy.mcu.rrrc_control import RevvyControl
from revvy.utils.emitter import SimpleEventEmitter
from revvy.utils.logger import get_logger


class PortDriver(ABC):
    """ A base class for motor and sensor drivers. """

    def __init__(self, port: 'PortInstance', driver_name: str):
        self._driver_name = driver_name
        self._port = port
        self._on_status_changed = SimpleEventEmitter()
        self.log = get_logger(driver_name, base=port.log)

    @property
    def driver_name(self):
        return self._driver_name

    @property
    def on_status_changed(self) -> SimpleEventEmitter:
        return self._on_status_changed

    def uninitialize(self):
        self._on_status_changed.clear()

    @abstractmethod
    def on_port_type_set(self):
        """ Performs driver-specific initialization as part of the port configuration. """
        pass

    @abstractmethod
    def update_status(self, data):
        """ Processes port-specific data coming from the MCU. """
        pass


class PortCollection:
    def __init__(self, ports):
        self._ports = list(ports)
        self._alias_map = {}

    @property
    def aliases(self):
        return self._alias_map

    def __getitem__(self, item):
        if type(item) is str:
            if item in self._alias_map.keys():
                item = self._alias_map[item]
            else:
                key_list = self._alias_map.keys()
                raise KeyError(f"key '{item}' not found in alias map. Available keys: {key_list}")
        return self._ports[item - 1]

    def __iter__(self):
        return self._ports.__iter__()


class PortHandler:
    """
    This class represents a port type (motor or sensor) and includes all ports of the same type.
    
    The class acts as a 1-based array so that users can index into it to get a specific port, or
    iterate over all ports.
    """
    def __init__(self, name, interface: RevvyControl, default_driver, amount: int, supported: dict, set_port_type):
        """
        Creates a new port handler for the given amount of ports.

        :param name: The name of the port type (e.g. "Motor" or "Sensor")
        :param interface: The RevvyControl instance to use for communication
        :param default_driver: The default driver to use for unconfigured ports
        :param amount: The amount of ports of this type
        :param supported: A dictionary of supported drivers
        :param set_port_type: A function that sets the port type on the MCU
        """
        self._log = get_logger(["PortHandler", name])
        self._types = supported
        self._port_count = amount
        self._ports = [
            PortInstance(
                i,
                f'{name}Port',
                interface,
                default_driver,
                supported,
                set_port_type
            )
            for i in range(1, amount + 1) 
        ]

    def __getitem__(self, port_idx: int) -> 'PortInstance':
        """
        Returns the port with the given index. We index ports from 1 so they correspond
        to port numbers on the Robot's enclosure.
        """

        if port_idx < 1 or port_idx > self._port_count:
            raise IndexError(f'Port index out of range: {port_idx}')

        return self._ports[port_idx - 1]

    def __iter__(self):
        return self._ports.__iter__()

    @property
    def available_types(self):
        """ Lists the names of the supported drivers """
        return self._types.keys()

    @property
    def port_count(self):
        return self._port_count

    def reset(self):
        for port in self:
            port.uninitialize()


class PortInstance:
    """
    A single motor or sensor port.
    
    This class is responsible for handling port configuration and driver initialization.
    """

    def __init__(self, port_idx, name, interface: RevvyControl, default_driver, supported, set_port_type):
        """
        
        :param port_idx: The index of the port (1-based)
        :param name: The name of the port type (e.g. "Motor" or "Sensor")
        :param interface: The RevvyControl instance to use for communication
        :param default_driver: The default driver to use for unconfigured ports
        :param supported: A dictionary of supported drivers
        :param set_port_type: A function that sets the port type on the MCU
        """
        self.log = get_logger(f'{name} {port_idx}', off=True)
        self._port_idx = port_idx
        self._interface = interface
        self._driver = default_driver(self)
        self._config_changed_callbacks = SimpleEventEmitter()
        self._supported = supported
        self._default_driver = default_driver
        self._set_port_type = set_port_type

    @property
    def id(self):
        return self._port_idx

    @property
    def interface(self):
        return self._interface

    @property
    def on_config_changed(self):
        """ Subscribe to port configuration changes """
        return self._config_changed_callbacks

    @property
    def driver(self) -> PortDriver:
        return self._driver

    def configure(self, config) -> PortDriver:
        """
        Configures the port with the given driver and configuration.
        If config is None, the port is set to not configured.
        """

        # Temporarily disable reading port by emitting an event that announced the port is not configured
        self._config_changed_callbacks(self, None)

        self.driver.uninitialize()

        if config is None:
            self._driver = self._default_driver(self)
        else:
            self._driver = config['driver'](self, config['config'])

        self.log(f'set to {self.driver.driver_name}')

        # TODO: it smells that we set the port type after the driver is created. It means we can't
        # use the constructor to perform the initialization.
        self._set_port_type(self.id, self._supported[self.driver.driver_name])
        self.driver.on_port_type_set()

        self._config_changed_callbacks(self, config)

        return self.driver

    def uninitialize(self):
        # self.log('Set to not configured')
        self.configure(None)

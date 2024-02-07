from abc import ABC, abstractmethod
from contextlib import suppress

from revvy.mcu.rrrc_control import RevvyControl
from revvy.utils.logger import get_logger


class SimpleEventEmitter:
    def __init__(self):
        self._callbacks = []

        self.add = self._callbacks.append
        self.clear = self._callbacks.clear

    def remove(self, callback):
        with suppress(ValueError):
            self._callbacks.remove(callback)

    def __call__(self, *args, **kwargs):
        for func in self._callbacks:
            func(*args, **kwargs)


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
    def on_status_changed(self):
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
    """ This class represents a port type (motor or sensor) and includes all ports of the same type. """
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

        # self._log(f'Created handler for {amount} ports')
        # self._log('Supported types:\n  {}'.format(", ".join(self.available_types)))

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

    # TODO: remove the attribute delegation to the driver. Instead, expose the driver as a property.
    props = ['log', '_port_idx', '_interface', '_driver', '_config_changed_callbacks', '_supported', '_default_driver', '_set_port_type']

    def __init__(self, port_idx, name, interface: RevvyControl, default_driver, supported, set_port_type):
        """
        
        :param port_idx: The index of the port (1-based)
        :param name: The name of the port type (e.g. "Motor" or "Sensor")
        :param interface: The RevvyControl instance to use for communication
        :param default_driver: The default driver to use for unconfigured ports
        :param supported: A dictionary of supported drivers
        :param set_port_type: A function that sets the port type on the MCU
        """
        self.log = get_logger(f'{name} {port_idx}')
        self._port_idx = port_idx
        self._interface = interface
        self._driver = None
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
        # Temporarily disable reading port by emitting an event that announced the port is not configured
        self._config_changed_callbacks(self, None)

        if self._driver:
            self._driver.uninitialize()

        if config is None:
            # self._log(f'set port {port.id} to not configured')
            driver = self._default_driver(self)
        else:
            driver = config['driver'](self, config['config'])

        # TODO: it smells that we set the port type after the driver is created. It means we can't
        # use the constructor to perform the initialization.
        self._set_port_type(self.id, self._supported[driver.driver_name])
        driver.on_port_type_set()

        self._driver = driver
        self._config_changed_callbacks(self, config)

        return self._driver

    def uninitialize(self):
        # self.log('Set to not configured')
        self.configure(None)

    # TODO: remove
    def __getattr__(self, key):
        return getattr(self._driver, key)

    # TODO: remove
    def __setattr__(self, key, value):
        if key in self.props:
            self.__dict__[key] = value
        else:
            setattr(self._driver, key, value)

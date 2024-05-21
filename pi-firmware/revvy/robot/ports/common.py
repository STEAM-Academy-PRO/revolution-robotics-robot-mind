"""
This module contains port driver implementations.

There are two kinds of ports: motor ports and sensor ports. The ports are grouped into
PortHandlers. Each port has a driver that implements the port's functionality.

The port drivers have counterparts on the MCU side. The PortHandler implementations read the
list of supported drivers from the MCU and this list can be used to map driver names to driver
IDs. The driver IDs are used to select the port drivers on the MCU.

The port drivers are responsible for handling the port's configuration and for sending commands and
processing the data coming from the MCU. The port drivers emit `on_status_changed` events whenever
the MCU reads new data from a particular port.
"""

from abc import ABC, abstractmethod
from collections.abc import Set
from typing import Generic, Iterator, NamedTuple, Optional, TypeVar

from revvy.mcu.rrrc_control import RevvyControl
from revvy.utils.emitter import SimpleEventEmitter
from revvy.utils.logger import LogLevel, get_logger


class PortDriver(ABC):
    """A base class for motor and sensor drivers."""

    def __init__(self, port: "PortInstance", driver_name: str, port_kind: str):
        self._driver_name = driver_name
        self._port = port
        self._on_status_changed = SimpleEventEmitter()
        self.log = get_logger([f"PortDriver[{port.id}]", port_kind, driver_name])

        self.log(f"Driver created", LogLevel.DEBUG)

    @property
    def driver_name(self) -> str:
        return self._driver_name

    @property
    def on_status_changed(self) -> SimpleEventEmitter:
        return self._on_status_changed

    def uninitialize(self) -> None:
        self._on_status_changed.clear()

    @abstractmethod
    def update_status(self, data: bytes):
        """Processes port-specific data coming from the MCU."""
        pass


class DriverConfig(NamedTuple):
    driver: type
    config: dict

    def create(self, port: "PortInstance"):
        """Creates a new driver instance for the given port."""
        return self.driver(port, self.config)


DriverType = TypeVar("DriverType", bound=PortDriver)


class PortHandler(Generic[DriverType]):
    """
    This class represents a port type (motor or sensor) and includes all ports of the same type.

    The class acts as an array so that users can index into it to get a specific port, or
    iterate over all ports.
    """

    def __init__(
        self,
        name,
        interface: RevvyControl,
        default_driver: DriverConfig,
        amount: int,
        supported: dict[str, int],
        set_port_type,
    ):
        """
        Creates a new port handler for the given amount of ports.

        :param name: The name of the port type (e.g. "Motor" or "Sensor")
        :param interface: The RevvyControl instance to use for communication
        :param default_driver: The default driver configuration to use for unconfigured ports
        :param amount: The amount of ports of this type
        :param supported: A dictionary of supported drivers
        :param set_port_type: A function that sets the port type on the MCU
        """
        self._log = get_logger(["PortHandler", name])
        self._types = supported
        self._port_count = amount
        self._ports = [
            PortInstance(i, name, interface, default_driver, supported, set_port_type)
            for i in range(amount)
        ]

    def __getitem__(self, port_idx: int) -> "PortInstance[DriverType]":
        """Returns the port with the given index."""

        try:
            return self._ports[port_idx]
        except IndexError as e:
            raise IndexError(f"Port index out of range: {port_idx}") from e

    def __iter__(self) -> Iterator["PortInstance[DriverType]"]:
        return self._ports.__iter__()

    @property
    def available_types(self) -> Set[str]:
        """Lists the names of the supported drivers"""
        return self._types.keys()

    @property
    def port_count(self) -> int:
        return self._port_count

    def reset(self) -> None:
        for port in self:
            port.uninitialize()


class PortInstance(Generic[DriverType]):
    """
    A single motor or sensor port.

    This class is responsible for handling port configuration and driver initialization.
    """

    def __init__(
        self,
        port_idx: int,
        name: str,
        interface: RevvyControl,
        default_driver: DriverConfig,
        supported,
        set_port_type,
    ):
        """
        :param port_idx: The index of the port (1-based)
        :param name: The name of the port type (e.g. "Motor" or "Sensor")
        :param interface: The RevvyControl instance to use for communication
        :param default_driver: The default driver config to use for unconfigured ports
        :param supported: A dictionary of supported drivers
        :param set_port_type: A function that sets the port type on the MCU
        """
        self.log = get_logger(["Port", name, str(port_idx)])
        self._port_idx = port_idx
        self._interface = interface
        self._config_changed_callbacks = SimpleEventEmitter()
        self._supported = supported
        self._default_driver = default_driver
        self._set_port_type = set_port_type
        self._driver: DriverType = default_driver.create(self)

    @property
    def id(self) -> int:
        return self._port_idx

    @property
    def interface(self) -> RevvyControl:
        return self._interface

    @property
    def on_config_changed(self) -> SimpleEventEmitter:
        """Port configuration change event emitter"""
        return self._config_changed_callbacks

    @property
    def driver(self) -> DriverType:
        return self._driver

    def configure(self, config: Optional["DriverConfig"]) -> DriverType:
        """
        Configures the port with the given driver and configuration.
        If config is None, the port is set to not configured.
        """

        was_unconfigured = type(self._driver) == self._default_driver.driver

        if not (was_unconfigured and config is None):
            # Temporarily disable reading port by emitting an event that announced the port is not configured
            self._config_changed_callbacks.trigger(self, None)

            self._driver.uninitialize()

            driver_config = config or self._default_driver
            self._driver = driver_config.create(self)
            self.log(f"set to {self.driver.driver_name}")

            self._config_changed_callbacks.trigger(self, config)

        return self.driver

    def uninitialize(self) -> None:
        # self.log('Set to not configured')
        self.configure(None)

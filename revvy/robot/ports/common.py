# SPDX-License-Identifier: GPL-3.0-only

from revvy.mcu.rrrc_control import RevvyControl


class PortCollection:
    def __init__(self, ports):
        self._ports = list(ports)
        self._alias_map = {}

    @property
    def aliases(self):
        return self._alias_map

    def __getitem__(self, item):
        if type(item) is str:
            item = self._alias_map[item]

        return self._ports[item - 1]

    def __iter__(self):
        return self._ports.__iter__()


class PortHandler:
    def __init__(self, interface: RevvyControl, drivers: dict, default_driver, amount: int, supported: dict):
        self._drivers = drivers
        self._types = supported
        self._port_count = amount
        self._default_driver = default_driver
        self._ports = {i: PortInstance(i, interface, self) for i in range(1, self.port_count + 1)}

    def __getitem__(self, port_idx):
        return self._ports[port_idx]

    def __iter__(self):
        return self._ports.values().__iter__()

    @property
    def available_types(self):
        """List of names of the supported drivers"""
        return self._types.values()

    @property
    def port_count(self):
        return self._port_count

    def reset(self):
        for port in self:
            port.uninitialize()

    def _set_port_type(self, port, port_type): raise NotImplementedError

    def configure_port(self, port, config):
        if config is None:
            print('PortInstance: set port {} to not configured'.format(port.id))
            self._set_port_type(port.id, self._types['NotConfigured'])

            driver = self._default_driver
        else:
            new_driver_name = config['driver']
            print('PortInstance: Configuring port {} to {}'.format(port.id, new_driver_name))
            driver = self._drivers[new_driver_name](port, config['config'])
            self._set_port_type(port.id, self._types[driver.driver])

            driver.on_port_type_set()

        return driver


class PortInstance:
    def __init__(self, port_idx, interface: RevvyControl, owner: PortHandler):
        self._port_idx = port_idx
        self._owner = owner
        self._interface = interface
        self._driver = None
        self._config_changed_callback = lambda port, cfg_name: None

    def on_config_changed(self, callback):
        self._config_changed_callback = callback

    def _notify_config_changed(self, config_name):
        self._config_changed_callback(self, config_name)

    def configure(self, config):
        self._notify_config_changed(None)  # temporarily disable reading port
        self._driver = self._owner.configure_port(self, config)
        self._notify_config_changed(config)

        return self._driver

    def uninitialize(self):
        self.configure(None)

    @property
    def interface(self):
        return self._interface

    @property
    def id(self):
        return self._port_idx

    def __getattr__(self, name):
        return self._driver.__getattribute__(name)

# SPDX-License-Identifier: GPL-3.0-only

from revvy.mcu.rrrc_control import RevvyControl
from revvy.robot.ports.common import PortHandler
from revvy.robot.ports.sensors.base import NullSensor
from revvy.robot.ports.sensors.ev3 import Ev3UARTSensor, ev3_color
from revvy.robot.ports.sensors.simple import bumper_switch, hcsr04


def create_sensor_port_handler(interface: RevvyControl):
    port_amount = interface.get_sensor_port_amount()
    port_types = interface.get_sensor_port_types()

    drivers = {
        'BumperSwitch': bumper_switch,
        'HC_SR04': hcsr04,
        'EV3': lambda port, _: Ev3UARTSensor(port),
        'EV3_Color': ev3_color
    }
    handler = PortHandler("Sensor", interface, drivers, NullSensor(), port_amount, port_types)
    handler._set_port_type = interface.set_sensor_port_type

    return handler

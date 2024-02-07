
from revvy.mcu.rrrc_control import RevvyControl
from revvy.robot.ports.common import PortHandler
from revvy.robot.ports.sensors.base import NullSensor


def create_sensor_port_handlers(interface: RevvyControl):
    port_amount = interface.get_sensor_port_amount()
    port_types = interface.get_sensor_port_types()

    return PortHandler("Sensor", interface, NullSensor, port_amount, port_types, interface.set_sensor_port_type)

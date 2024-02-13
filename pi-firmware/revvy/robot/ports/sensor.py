from revvy.mcu.rrrc_control import RevvyControl
from revvy.robot.ports.common import PortHandler
from revvy.robot.ports.sensors.base import NullSensor

class SensorPortHandler(PortHandler):
    def __init__(self, interface: RevvyControl):
        port_amount = interface.get_sensor_port_amount()
        port_types = interface.get_sensor_port_types()

        super().__init__("Sensor", interface, NullSensor, port_amount, port_types, interface.set_sensor_port_type)

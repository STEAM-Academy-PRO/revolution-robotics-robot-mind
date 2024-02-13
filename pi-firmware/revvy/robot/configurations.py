from revvy.robot.ports.motors.dc_motor import DcMotorController
from revvy.robot.ports.sensors.simple import BumperSwitch, Hcsr04, ColorSensor


class Motors:
    RevvyMotor = {
        'driver': DcMotorController,
        'config': {
            'speed_controller': [0.6065, 0.3935, 0, -150, 150],
            'position_controller': [0.1, 0.0000, 0, -150, 150],
            'acceleration_limits': [500, 500],
            'max_current': 1.5,
            'linearity': {0.5: 0, 5.0154: 18, 37.0370: 60, 67.7083: 100, 97.4151: 140, 144.0972: 200},
            'encoder_resolution': 12,
            'gear_ratio': 64.8
        }
    }
    RevvyMotor_CCW = {
        'driver': DcMotorController,
        'config': {
            'speed_controller': [0.6065, 0.3935, 0, -150, 150],
            'position_controller': [0.1, 0.0000, 0, -150, 150],
            'acceleration_limits': [500, 500],
            'max_current': 1.5,
            'linearity': {0.5: 0, 5.0154: 18, 37.0370: 60, 67.7083: 100, 97.4151: 140, 144.0972: 200},
            'encoder_resolution': -12,
            'gear_ratio': 64.8
        }
    }


# TODO: named tuples instead of dicts
class Sensors:
    Ultrasonic = {
        'driver': Hcsr04,
        'config': {}
    }
    BumperSwitch = {
        'driver': BumperSwitch,
        'config': {}
    }
    SofteqCS = {
        'driver': ColorSensor,
        'config': {}
    }

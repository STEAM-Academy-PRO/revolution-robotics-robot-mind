from revvy.robot.ports.common import DriverConfig
from revvy.robot.ports.motors.dc_motor import DcMotorController, PositionThreshold
from revvy.robot.ports.sensors.simple import BumperSwitch, Hcsr04, ColorSensor


# TODO: Right now we're pairing the driver type and the configuration. Instead, we should
# create configuration objects that can create the driver instances. This way, we can
# document the configuration options.
class Motors:
    RevvyMotor = DriverConfig(
        driver=DcMotorController,
        config={
            # sped units are ticks / 10ms
            # P, I, D are dimensionless regulator coefficients
            "speed_controller": [0.4, 0.5, 0.8, -150, 150],  # P, I, D, min speed, max speed
            "position_controller": {
                "slow": [0.1, 0.0, 0.0, -150, 150],  # P, I, D, min speed, max speed
                "fast": [0.8, 0.0, 1.5, -150, 150],  # P, I, D, min speed, max speed
                # Distance from goal where we switch to the slow controller
                "fast_threshold": PositionThreshold.degrees(5),
            },
            # max deceleration, max acceleration, in units of `[speed units] / 10ms`
            "acceleration_limits": [500, 500],
            "max_current": 1.5,  # Amps
            # The identified motor characteristic: (input PWM value, output speed)
            "linearity": [
                (0.5, 0),
                (5.0154, 18),
                (37.0370, 60),
                (67.7083, 100),
                (97.4151, 140),
                (144.0972, 200),
            ],
            "encoder_resolution": 12,  # The number of ticks per revolution
            "gear_ratio": 64.8,  # The gear ratio of the motor. It takes this many revolutions of the motor axle to turn the wheel once.
        },
    )
    RevvyMotor_CCW = DriverConfig(
        driver=DcMotorController,
        config={
            "speed_controller": [0.4, 0.5, 0.8, -150, 150],
            "position_controller": {
                "slow": [0.1, 0.0, 0.0, -150, 150],
                "fast": [0.8, 0.0, 1.5, -150, 150],
                "fast_threshold": PositionThreshold.degrees(5),
            },
            "acceleration_limits": [500, 500],
            "max_current": 1.5,
            "linearity": [
                (0.5, 0),
                (5.0154, 18),
                (37.0370, 60),
                (67.7083, 100),
                (97.4151, 140),
                (144.0972, 200),
            ],
            "encoder_resolution": -12,
            "gear_ratio": 64.8,
        },
    )


class Sensors:
    Ultrasonic = DriverConfig(driver=Hcsr04, config={})

    BumperSwitch = DriverConfig(driver=BumperSwitch, config={})

    SofteqCS = DriverConfig(driver=ColorSensor, config={})

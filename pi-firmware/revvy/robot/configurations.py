from revvy.robot.ports.common import DriverConfig
from revvy.robot.ports.motors.dc_motor import (
    DcMotorController,
    EmulatedDcMotorController,
    PidConfig,
    PositionThreshold,
    TwoValuePidConfig,
)
from revvy.robot.ports.sensors.simple import BumperSwitch, Hcsr04, ColorSensor


DC_MOTOR_SPEED_PID = PidConfig(
    p=0.4,
    i=0.5,
    d=0.8,
    # Minimum and maximum output PWM.
    # These values are not scaled with the linearity table,
    # as opposed to user-specified power limits. The timers driving the motors have a range of
    # -200 to 200.
    lower_output_limit=-200,
    upper_output_limit=200,
)

# sped units are ticks / 10ms
DC_MOTOR_POSITION_PID_SLOW = PidConfig(
    p=0.1,
    i=0.0,
    d=0.0,
    # min speed
    lower_output_limit=-150,
    # max speed
    upper_output_limit=150,
)
DC_MOTOR_POSITION_PID_FAST = PidConfig(
    p=0.8,
    i=0.0,
    d=1.5,
    # min speed
    lower_output_limit=-150,
    # max speed
    upper_output_limit=150,
)
DC_MOTOR_POSITION_CONFIG = TwoValuePidConfig(
    slow=DC_MOTOR_POSITION_PID_SLOW,
    fast=DC_MOTOR_POSITION_PID_FAST,
    fast_threshold=PositionThreshold.degrees(5),
)


DC_MOTOR_LINEARITY_TABLE = [
    (0.5, 0),
    (5.0154, 18),
    (37.0370, 60),
    (67.7083, 100),
    (97.4151, 140),
    (144.0972, 200),
]
"""The identified motor characteristic: (output speed, input PWM value)"""


# TODO: Right now we're pairing the driver type and the configuration. Instead, we should
# create configuration objects that can create the driver instances. This way, we can
# document the configuration options.
class Motors:
    RevvyMotor = DriverConfig(
        driver=DcMotorController,
        config={
            "speed_controller": DC_MOTOR_SPEED_PID,
            "position_controller": DC_MOTOR_POSITION_CONFIG,
            # max deceleration, max acceleration, in units of `[speed units] / 10ms` (?)
            "acceleration_limits": [500, 500],
            "max_current": 1.5,  # Amps
            "linearity": DC_MOTOR_LINEARITY_TABLE,
            "encoder_resolution": 12,  # The number of ticks per revolution
            "gear_ratio": 64.8,  # The gear ratio of the motor. It takes this many revolutions of the motor axle to turn the wheel once.
        },
    )
    EmulatedRevvyMotor = DriverConfig(
        driver=EmulatedDcMotorController,
        config={
            "speed_controller": DC_MOTOR_SPEED_PID,
            "position_controller": DC_MOTOR_POSITION_CONFIG,
            # max deceleration, max acceleration, in units of `[speed units] / 10ms` (?)
            "acceleration_limits": [500, 500],
            "max_current": 1.5,  # Amps
            "linearity": [(200, 200)],  # emulated motors are linear. First point (0, 0) is implied.
            "encoder_resolution": 12,  # The number of ticks per revolution
            "gear_ratio": 64.8,  # The gear ratio of the motor. It takes this many revolutions of the motor axle to turn the wheel once.
        },
    )


def ccw_motor(config: DriverConfig) -> DriverConfig:
    """Returns a new configuration with the encoder resolution negated. This causes the motor to
    rotate in the opposite direction."""
    return DriverConfig(
        driver=config.driver,
        config={
            **config.config,
            "encoder_resolution": -config.config["encoder_resolution"],
        },
    )


class Sensors:
    Ultrasonic = DriverConfig(driver=Hcsr04, config={})

    BumperSwitch = DriverConfig(driver=BumperSwitch, config={})

    SofteqCS = DriverConfig(driver=ColorSensor, config={})

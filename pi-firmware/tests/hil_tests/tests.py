import time
from revvy.utils.logger import Logger
from tests.hil_tests.hil_test_utils.runner import run_test_scenarios, with_timeout

# IMPORTANT: make sure to import dependencies after this comment. Doing it before may break the
# in-memory log collector and spam logs.
from revvy.robot.configurations import Motors, ccw_motor
from revvy.api.programmed import ProgrammedRobotController
from revvy.robot.robot_events import RobotEvent
from revvy.robot_config import RobotConfig

from revvy.robot_manager import RevvyStatusCode
from revvy.utils.functions import b64_encode_str


def can_play_sound(log: Logger, controller: ProgrammedRobotController):
    """A test case that configures a script to play a sound when a remote controller button is pressed."""

    def fail_on_script_error(*e) -> None:
        # In this test, if we encounter an error, let's just stop and exit
        controller.robot_manager.exit(RevvyStatusCode.ERROR)

    controller.robot_manager.on(RobotEvent.ERROR, fail_on_script_error)

    config = RobotConfig()
    config.process_script(
        {
            "assignments": {"buttons": [{"id": 1, "priority": 0}]},
            "pythonCode": b64_encode_str("""robot.play_tune("yee_haw")"""),
        },
        0,
    )

    controller.configure(config)

    log("Trying to play sound")
    controller.press_button(1)


@with_timeout(2)
def can_stop_script_with_long_sleep(log: Logger, controller: ProgrammedRobotController):
    """A test case that configures a script to sleep for a long time. We then stop the script by pressing a button."""

    def fail_on_script_error(*e) -> None:
        # In this test, if we encounter an error, let's just stop and exit
        controller.robot_manager.exit(RevvyStatusCode.ERROR)

    controller.robot_manager.on(RobotEvent.ERROR, fail_on_script_error)

    config = RobotConfig()
    config.process_script(
        {
            "assignments": {"buttons": [{"id": 1, "priority": 0}]},
            "pythonCode": b64_encode_str("""time.sleep(10000)"""),
        },
        0,
    )

    controller.configure(config)

    log("Start script")
    controller.press_button(1)

    time.sleep(0.2)

    log("Stop script")
    controller.press_button(1)

    controller.wait_for_scripts_to_end()


def test_motor_for_i2c_bug(log: Logger, controller: ProgrammedRobotController):
    # I'm using this test locally to test a non-deterministic I2C bug.
    def fail_on_script_error(*e) -> None:
        # In this test, if we encounter an error, let's just stop and exit
        controller.robot_manager.exit(RevvyStatusCode.ERROR)

    controller.robot_manager.on(RobotEvent.ERROR, fail_on_script_error)

    controller.robot_manager.robot._robot_control.test_motor_on_port(6, 60, 10)


@with_timeout(2)
def sensors_can_be_read(log: Logger, controller: ProgrammedRobotController):
    """A test case that configures a script to read sensors."""

    def fail_on_script_error(*e) -> None:
        # In this test, if we encounter an error, let's just stop and exit
        controller.robot_manager.exit(RevvyStatusCode.ERROR)

    controller.robot_manager.on(RobotEvent.ERROR, fail_on_script_error)
    # TODO: sensors should not wait for data, but provide a default

    config = RobotConfig()
    config.add_motor(None, "motor1")
    config.add_motor(None, "motor2")
    config.add_motor(None, "motor3")
    config.add_motor(Motors.EmulatedRevvyMotor, "motor4")
    config.add_motor(None, "motor5")
    config.add_motor(None, "motor6")

    config.add_sensor_from_json({"type": 1, "name": "distance_sensor"})
    config.add_sensor_from_json(None)
    config.add_sensor_from_json({"type": 2, "name": "button"})
    config.add_sensor_from_json({"type": 4, "name": "color_sensor"})

    config.process_script(
        {
            "assignments": {"buttons": [{"id": 1, "priority": 0}]},
            "pythonCode": b64_encode_str(
                """
# different ways to read the gyroscope
robot.imu.orientation.yaw
robot.imu.yaw_angle

# sensor peripherals
robot.sensors["distance_sensor"].read()
robot.sensors["button"].read()
robot.read_color(4)
robot.read_hue(4)

# motor peripherals
robot.motors["motor4"].pos
"""
            ),
        },
        0,
    )

    controller.configure(config)

    log("Start script")
    controller.press_button(1)

    controller.wait_for_scripts_to_end()


@with_timeout(30)
def motors_dont_cause_errors(log: Logger, controller: ProgrammedRobotController):
    """
    A test case that configures a script to drive the robot and motors. Since no motors and
    motor battery are connected, the blocks should essentially be no-op. However, this test
    still verifies that motor commands reach the MCU and don't cause errors.
    """

    def fail_on_script_error(*e) -> None:
        # In this test, if we encounter an error, let's just stop and exit
        controller.robot_manager.exit(RevvyStatusCode.ERROR)

    controller.robot_manager.on(RobotEvent.ERROR, fail_on_script_error)

    config = RobotConfig()
    config.add_motor(ccw_motor(Motors.EmulatedRevvyMotor), "motor1")
    config.add_motor(Motors.EmulatedRevvyMotor, "motor2")
    config.add_motor(None, "motor3")
    config.add_motor(Motors.EmulatedRevvyMotor, "motor4")
    config.add_motor(None, "motor5")
    config.add_motor(None, "motor6")

    config.drivetrain.left.append(1)
    config.drivetrain.right.append(2)

    config.process_script(
        {
            "assignments": {"buttons": [{"id": 1, "priority": 0}]},
            "pythonCode": b64_encode_str(
                """
#
# drive blockly options
#
robot.drivetrain.set_speed(direction=Motor.DIRECTION_FWD, speed=75, unit_speed=Motor.UNIT_SPEED_RPM)
robot.drivetrain.set_speed(direction=Motor.DIRECTION_FWD, speed=75, unit_speed=Motor.UNIT_SPEED_PWR)
robot.drivetrain.set_speed(direction=Motor.DIRECTION_BACK, speed=75, unit_speed=Motor.UNIT_SPEED_RPM)
robot.drivetrain.set_speed(direction=Motor.DIRECTION_BACK, speed=75, unit_speed=Motor.UNIT_SPEED_PWR)

robot.drive(direction=Motor.DIRECTION_FWD, rotation=0.1, unit_rotation=Motor.UNIT_SEC, speed=75, unit_speed=Motor.UNIT_SPEED_RPM)
robot.drive(direction=Motor.DIRECTION_FWD, rotation=0.1, unit_rotation=Motor.UNIT_SEC, speed=75, unit_speed=Motor.UNIT_SPEED_PWR)
robot.drive(direction=Motor.DIRECTION_FWD, rotation=3, unit_rotation=Motor.UNIT_ROT, speed=75, unit_speed=Motor.UNIT_SPEED_RPM)
robot.drive(direction=Motor.DIRECTION_FWD, rotation=3, unit_rotation=Motor.UNIT_ROT, speed=75, unit_speed=Motor.UNIT_SPEED_PWR)
robot.drive(direction=Motor.DIRECTION_BACK, rotation=0.1, unit_rotation=Motor.UNIT_SEC, speed=75, unit_speed=Motor.UNIT_SPEED_RPM)
robot.drive(direction=Motor.DIRECTION_BACK, rotation=0.1, unit_rotation=Motor.UNIT_SEC, speed=75, unit_speed=Motor.UNIT_SPEED_PWR)
robot.drive(direction=Motor.DIRECTION_BACK, rotation=3, unit_rotation=Motor.UNIT_ROT, speed=75, unit_speed=Motor.UNIT_SPEED_RPM)
robot.drive(direction=Motor.DIRECTION_BACK, rotation=3, unit_rotation=Motor.UNIT_ROT, speed=75, unit_speed=Motor.UNIT_SPEED_PWR)

# blockly only generates unit_speed=RPM
# beware that UNIT_TURN_ANGLE turns take 3 seconds to time out
robot.turn(direction=Motor.DIRECTION_LEFT, rotation=90, unit_rotation=Motor.UNIT_TURN_ANGLE, speed=75, unit_speed=Motor.UNIT_SPEED_RPM)
robot.turn(direction=Motor.DIRECTION_LEFT, rotation=0.1, unit_rotation=Motor.UNIT_SEC, speed=75, unit_speed=Motor.UNIT_SPEED_RPM)
robot.turn(direction=Motor.DIRECTION_RIGHT, rotation=90, unit_rotation=Motor.UNIT_TURN_ANGLE, speed=75, unit_speed=Motor.UNIT_SPEED_RPM)
robot.turn(direction=Motor.DIRECTION_RIGHT, rotation=0.1, unit_rotation=Motor.UNIT_SEC, speed=75, unit_speed=Motor.UNIT_SPEED_RPM)
#
# motor blockly options
#
robot.motors["motor4"].move(direction=Motor.DIRECTION_FWD, amount=0.1, unit_amount=Motor.UNIT_SEC, limit=75, unit_limit=Motor.UNIT_SPEED_RPM)
robot.motors["motor4"].move(direction=Motor.DIRECTION_FWD, amount=0.1, unit_amount=Motor.UNIT_SEC, limit=75, unit_limit=Motor.UNIT_SPEED_PWR)
robot.motors["motor4"].move(direction=Motor.DIRECTION_FWD, amount=3, unit_amount=Motor.UNIT_DEG, limit=75, unit_limit=Motor.UNIT_SPEED_RPM)
robot.motors["motor4"].move(direction=Motor.DIRECTION_FWD, amount=3, unit_amount=Motor.UNIT_DEG, limit=75, unit_limit=Motor.UNIT_SPEED_PWR)
robot.motors["motor4"].move(direction=Motor.DIRECTION_FWD, amount=3, unit_amount=Motor.UNIT_ROT, limit=75, unit_limit=Motor.UNIT_SPEED_RPM)
robot.motors["motor4"].move(direction=Motor.DIRECTION_FWD, amount=3, unit_amount=Motor.UNIT_ROT, limit=75, unit_limit=Motor.UNIT_SPEED_PWR)
robot.motors["motor4"].move(direction=Motor.DIRECTION_BACK, amount=0.1, unit_amount=Motor.UNIT_SEC, limit=75, unit_limit=Motor.UNIT_SPEED_RPM)
robot.motors["motor4"].move(direction=Motor.DIRECTION_BACK, amount=0.1, unit_amount=Motor.UNIT_SEC, limit=75, unit_limit=Motor.UNIT_SPEED_PWR)
robot.motors["motor4"].move(direction=Motor.DIRECTION_BACK, amount=3, unit_amount=Motor.UNIT_DEG, limit=75, unit_limit=Motor.UNIT_SPEED_RPM)
robot.motors["motor4"].move(direction=Motor.DIRECTION_BACK, amount=3, unit_amount=Motor.UNIT_DEG, limit=75, unit_limit=Motor.UNIT_SPEED_PWR)
robot.motors["motor4"].move(direction=Motor.DIRECTION_BACK, amount=3, unit_amount=Motor.UNIT_ROT, limit=75, unit_limit=Motor.UNIT_SPEED_RPM)
robot.motors["motor4"].move(direction=Motor.DIRECTION_BACK, amount=3, unit_amount=Motor.UNIT_ROT, limit=75, unit_limit=Motor.UNIT_SPEED_PWR)
robot.motors["motor4"].spin(direction=Motor.DIRECTION_FWD, rotation=75, unit_rotation=Motor.UNIT_SPEED_RPM)
robot.motors["motor4"].spin(direction=Motor.DIRECTION_FWD, rotation=75, unit_rotation=Motor.UNIT_SPEED_PWR)
robot.motors["motor4"].spin(direction=Motor.DIRECTION_BACK, rotation=75, unit_rotation=Motor.UNIT_SPEED_RPM)
robot.motors["motor4"].spin(direction=Motor.DIRECTION_BACK, rotation=75, unit_rotation=Motor.UNIT_SPEED_PWR)
robot.motors["motor4"].stop(action=Motor.ACTION_STOP_AND_HOLD)
robot.motors["motor4"].stop(action=Motor.ACTION_RELEASE)

for motor in robot.motors:
  motor.stop(action=Motor.ACTION_STOP_AND_HOLD)

for motor2 in robot.motors:
  motor2.stop(action=Motor.ACTION_RELEASE)

robot.motors["motor4"].pos = 0
"""
            ),
        },
        0,
    )

    controller.configure(config)

    log("Start script")
    controller.press_button(1)

    controller.wait_for_scripts_to_end()


@with_timeout(20)
def missing_motor_does_not_block_script(log: Logger, controller: ProgrammedRobotController):
    """
    A test case that configures a script to drive a motors. Since no motors and
    motor battery are connected, the motor should quickly report a BLOCKED status and the script
    should move on.
    """

    def fail_on_script_error(*e) -> None:
        # In this test, if we encounter an error, let's just stop and exit
        controller.robot_manager.exit(RevvyStatusCode.ERROR)

    controller.robot_manager.on(RobotEvent.ERROR, fail_on_script_error)

    config = RobotConfig()
    # intentionally not EmulatedRevvyMotor to test blocking behaviour
    config.add_motor(ccw_motor(Motors.RevvyMotor), "motor1")
    config.add_motor(None, "motor2")
    config.add_motor(None, "motor3")
    config.add_motor(None, "motor4")
    config.add_motor(None, "motor5")
    config.add_motor(None, "motor6")

    config.drivetrain.left.append(1)

    config.process_script(
        {
            "assignments": {"buttons": [{"id": 1, "priority": 0}]},
            "pythonCode": b64_encode_str(
                """
#
# drive blockly options
#
robot.drivetrain.set_speed(direction=Motor.DIRECTION_FWD, speed=75, unit_speed=Motor.UNIT_SPEED_RPM)
robot.drivetrain.set_speed(direction=Motor.DIRECTION_FWD, speed=75, unit_speed=Motor.UNIT_SPEED_PWR)
robot.drivetrain.set_speed(direction=Motor.DIRECTION_BACK, speed=75, unit_speed=Motor.UNIT_SPEED_RPM)
robot.drivetrain.set_speed(direction=Motor.DIRECTION_BACK, speed=75, unit_speed=Motor.UNIT_SPEED_PWR)

robot.drive(direction=Motor.DIRECTION_FWD, rotation=0.1, unit_rotation=Motor.UNIT_SEC, speed=75, unit_speed=Motor.UNIT_SPEED_RPM)
robot.drive(direction=Motor.DIRECTION_FWD, rotation=0.1, unit_rotation=Motor.UNIT_SEC, speed=75, unit_speed=Motor.UNIT_SPEED_PWR)
robot.drive(direction=Motor.DIRECTION_FWD, rotation=3, unit_rotation=Motor.UNIT_ROT, speed=75, unit_speed=Motor.UNIT_SPEED_RPM)
robot.drive(direction=Motor.DIRECTION_FWD, rotation=3, unit_rotation=Motor.UNIT_ROT, speed=75, unit_speed=Motor.UNIT_SPEED_PWR)
robot.drive(direction=Motor.DIRECTION_BACK, rotation=0.1, unit_rotation=Motor.UNIT_SEC, speed=75, unit_speed=Motor.UNIT_SPEED_RPM)
robot.drive(direction=Motor.DIRECTION_BACK, rotation=0.1, unit_rotation=Motor.UNIT_SEC, speed=75, unit_speed=Motor.UNIT_SPEED_PWR)
robot.drive(direction=Motor.DIRECTION_BACK, rotation=3, unit_rotation=Motor.UNIT_ROT, speed=75, unit_speed=Motor.UNIT_SPEED_RPM)
robot.drive(direction=Motor.DIRECTION_BACK, rotation=3, unit_rotation=Motor.UNIT_ROT, speed=75, unit_speed=Motor.UNIT_SPEED_PWR)

# blockly only generates unit_speed=RPM
# beware that UNIT_TURN_ANGLE turns take 3 seconds to time out
robot.turn(direction=Motor.DIRECTION_LEFT, rotation=90, unit_rotation=Motor.UNIT_TURN_ANGLE, speed=75, unit_speed=Motor.UNIT_SPEED_RPM)
robot.turn(direction=Motor.DIRECTION_LEFT, rotation=0.1, unit_rotation=Motor.UNIT_SEC, speed=75, unit_speed=Motor.UNIT_SPEED_RPM)
robot.turn(direction=Motor.DIRECTION_RIGHT, rotation=90, unit_rotation=Motor.UNIT_TURN_ANGLE, speed=75, unit_speed=Motor.UNIT_SPEED_RPM)
robot.turn(direction=Motor.DIRECTION_RIGHT, rotation=0.1, unit_rotation=Motor.UNIT_SEC, speed=75, unit_speed=Motor.UNIT_SPEED_RPM)
#
# motor blockly options
#
robot.motors["motor1"].move(direction=Motor.DIRECTION_FWD, amount=0.1, unit_amount=Motor.UNIT_SEC, limit=75, unit_limit=Motor.UNIT_SPEED_RPM)
robot.motors["motor1"].move(direction=Motor.DIRECTION_FWD, amount=0.1, unit_amount=Motor.UNIT_SEC, limit=75, unit_limit=Motor.UNIT_SPEED_PWR)
robot.motors["motor1"].move(direction=Motor.DIRECTION_FWD, amount=3, unit_amount=Motor.UNIT_DEG, limit=75, unit_limit=Motor.UNIT_SPEED_RPM)
robot.motors["motor1"].move(direction=Motor.DIRECTION_FWD, amount=3, unit_amount=Motor.UNIT_DEG, limit=75, unit_limit=Motor.UNIT_SPEED_PWR)
robot.motors["motor1"].move(direction=Motor.DIRECTION_FWD, amount=3, unit_amount=Motor.UNIT_ROT, limit=75, unit_limit=Motor.UNIT_SPEED_RPM)
robot.motors["motor1"].move(direction=Motor.DIRECTION_FWD, amount=3, unit_amount=Motor.UNIT_ROT, limit=75, unit_limit=Motor.UNIT_SPEED_PWR)
robot.motors["motor1"].spin(direction=Motor.DIRECTION_FWD, rotation=75, unit_rotation=Motor.UNIT_SPEED_RPM)
robot.motors["motor1"].spin(direction=Motor.DIRECTION_FWD, rotation=75, unit_rotation=Motor.UNIT_SPEED_PWR)
robot.motors["motor1"].stop(action=Motor.ACTION_RELEASE)
"""
            ),
        },
        0,
    )

    controller.configure(config)

    log("Start script")
    controller.press_button(1)

    controller.wait_for_scripts_to_end()


def trying_to_access_uncofigured_motor_raises_error(
    log: Logger, controller: ProgrammedRobotController
):
    error_raised = False

    def fail_on_script_error(*e) -> None:
        nonlocal error_raised
        error_raised = True

    controller.robot_manager.on(RobotEvent.ERROR, fail_on_script_error)

    config = RobotConfig()
    config.add_motor(ccw_motor(Motors.EmulatedRevvyMotor), "motor1")
    config.add_motor(Motors.EmulatedRevvyMotor, "motor2")
    config.add_motor(Motors.EmulatedRevvyMotor, "motor3")
    config.add_motor(None, "motor4")
    config.add_motor(None, "motor5")
    config.add_motor(None, "motor6")

    config.drivetrain.left.append(1)
    config.drivetrain.right.append(2)

    config.process_script(
        {
            "assignments": {"buttons": [{"id": 1, "priority": 0}]},
            "pythonCode": b64_encode_str(
                """
robot.motors["motor4"].pos
"""
            ),
        },
        0,
    )

    controller.configure(config)

    log("Start script")
    controller.press_button(1)

    controller.wait_for_scripts_to_end()

    if not error_raised:
        # In this test, if we DO NOT  encounter an error, that is a failure
        log("Expected error was not raised")
        controller.robot_manager.exit(RevvyStatusCode.ERROR)


@with_timeout(30)
def trying_to_drive_without_drivetrain_motors_is_no_op(
    log: Logger, controller: ProgrammedRobotController
):

    def fail_on_script_error(*e) -> None:
        # In this test, if we encounter an error, let's just stop and exit
        controller.robot_manager.exit(RevvyStatusCode.ERROR)

    controller.robot_manager.on(RobotEvent.ERROR, fail_on_script_error)

    config = RobotConfig()
    config.add_motor(None, "motor1")
    config.add_motor(None, "motor2")
    config.add_motor(None, "motor3")
    config.add_motor(Motors.EmulatedRevvyMotor, "motor4")
    config.add_motor(None, "motor5")
    config.add_motor(None, "motor6")

    config.process_script(
        {
            "assignments": {"buttons": [{"id": 1, "priority": 0}]},
            "pythonCode": b64_encode_str(
                """
#
# drive blockly options
#
robot.drivetrain.set_speed(direction=Motor.DIRECTION_FWD, speed=75, unit_speed=Motor.UNIT_SPEED_RPM)
robot.drivetrain.set_speed(direction=Motor.DIRECTION_FWD, speed=75, unit_speed=Motor.UNIT_SPEED_PWR)
robot.drivetrain.set_speed(direction=Motor.DIRECTION_BACK, speed=75, unit_speed=Motor.UNIT_SPEED_RPM)
robot.drivetrain.set_speed(direction=Motor.DIRECTION_BACK, speed=75, unit_speed=Motor.UNIT_SPEED_PWR)

robot.drive(direction=Motor.DIRECTION_FWD, rotation=0.1, unit_rotation=Motor.UNIT_SEC, speed=75, unit_speed=Motor.UNIT_SPEED_RPM)
robot.drive(direction=Motor.DIRECTION_FWD, rotation=0.1, unit_rotation=Motor.UNIT_SEC, speed=75, unit_speed=Motor.UNIT_SPEED_PWR)
robot.drive(direction=Motor.DIRECTION_FWD, rotation=3, unit_rotation=Motor.UNIT_ROT, speed=75, unit_speed=Motor.UNIT_SPEED_RPM)
robot.drive(direction=Motor.DIRECTION_FWD, rotation=3, unit_rotation=Motor.UNIT_ROT, speed=75, unit_speed=Motor.UNIT_SPEED_PWR)
robot.drive(direction=Motor.DIRECTION_BACK, rotation=0.1, unit_rotation=Motor.UNIT_SEC, speed=75, unit_speed=Motor.UNIT_SPEED_RPM)
robot.drive(direction=Motor.DIRECTION_BACK, rotation=0.1, unit_rotation=Motor.UNIT_SEC, speed=75, unit_speed=Motor.UNIT_SPEED_PWR)
robot.drive(direction=Motor.DIRECTION_BACK, rotation=3, unit_rotation=Motor.UNIT_ROT, speed=75, unit_speed=Motor.UNIT_SPEED_RPM)
robot.drive(direction=Motor.DIRECTION_BACK, rotation=3, unit_rotation=Motor.UNIT_ROT, speed=75, unit_speed=Motor.UNIT_SPEED_PWR)

# blockly only generates unit_speed=RPM
robot.turn(direction=Motor.DIRECTION_LEFT, rotation=90, unit_rotation=Motor.UNIT_TURN_ANGLE, speed=75, unit_speed=Motor.UNIT_SPEED_RPM)
robot.turn(direction=Motor.DIRECTION_LEFT, rotation=0.1, unit_rotation=Motor.UNIT_SEC, speed=75, unit_speed=Motor.UNIT_SPEED_RPM)
robot.turn(direction=Motor.DIRECTION_RIGHT, rotation=90, unit_rotation=Motor.UNIT_TURN_ANGLE, speed=75, unit_speed=Motor.UNIT_SPEED_RPM)
robot.turn(direction=Motor.DIRECTION_RIGHT, rotation=0.1, unit_rotation=Motor.UNIT_SEC, speed=75, unit_speed=Motor.UNIT_SPEED_RPM)

for motor in robot.motors:
  motor.stop(action=Motor.ACTION_STOP_AND_HOLD)

for motor2 in robot.motors:
  motor2.stop(action=Motor.ACTION_RELEASE)
"""
            ),
        },
        0,
    )

    controller.configure(config)

    log("Start script")
    controller.press_button(1)

    controller.wait_for_scripts_to_end()


def trying_to_access_uncofigured_sensor_raises_error(
    log: Logger, controller: ProgrammedRobotController
):
    """A test case that configures a script to read sensors, but the sensors are not configured. We expect an error to be raised."""

    error_raised = False

    def expect_script_error(*e) -> None:
        nonlocal error_raised
        error_raised = True

    controller.robot_manager.on(RobotEvent.ERROR, expect_script_error)

    config = RobotConfig()
    config.process_script(
        {
            "assignments": {"buttons": [{"id": 1, "priority": 0}]},
            "pythonCode": b64_encode_str(
                """
robot.sensors["distance_sensor"].read()
"""
            ),
        },
        0,
    )

    controller.configure(config)

    log("Start script")
    controller.press_button(1)

    controller.wait_for_scripts_to_end()

    if not error_raised:
        log("Expected error was not raised")
        controller.robot_manager.exit(RevvyStatusCode.ERROR)


def failing_to_take_resource_from_lower_prio_script_should_not_error(
    log: Logger, controller: ProgrammedRobotController
):
    """
    While the exactly expected behaviour is currently undefined, an AttributeError due to an
    incorrect resource handle is definitely not what we want.
    """

    def fail_on_script_error(*e) -> None:
        # In this test, if we encounter an error, let's just stop and exit
        controller.robot_manager.exit(RevvyStatusCode.ERROR)

    controller.robot_manager.on(RobotEvent.ERROR, fail_on_script_error)

    config = RobotConfig()
    config.add_motor(Motors.EmulatedRevvyMotor, "motor1")

    config.process_script(
        {
            "assignments": {"buttons": [{"id": 1, "priority": 1}, {"id": 2, "priority": 2}]},
            "pythonCode": b64_encode_str(
                """
while True:
  robot.motors["motor1"].move(direction=Motor.DIRECTION_FWD, amount=3, unit_amount=Motor.UNIT_SEC, limit=75, unit_limit=Motor.UNIT_SPEED_RPM)
"""
            ),
        },
        0,
    )
    config.process_script(
        {
            "assignments": {"buttons": [{"id": 3, "priority": 1}]},
            "pythonCode": b64_encode_str(
                """
Control.terminate_all()
"""
            ),
        },
        0,
    )

    controller.configure(config)

    controller.press_button(1)
    time.sleep(0.5)
    controller.press_button(2)

    # force infinite loops to stop
    controller.press_button(3)

    controller.wait_for_scripts_to_end()


if __name__ == "__main__":
    run_test_scenarios(
        [
            can_play_sound,
            can_stop_script_with_long_sleep,
            sensors_can_be_read,
            test_motor_for_i2c_bug,
            motors_dont_cause_errors,
            missing_motor_does_not_block_script,
            trying_to_access_uncofigured_motor_raises_error,
            trying_to_access_uncofigured_sensor_raises_error,
            trying_to_drive_without_drivetrain_motors_is_no_op,
            failing_to_take_resource_from_lower_prio_script_should_not_error,
        ]
    )

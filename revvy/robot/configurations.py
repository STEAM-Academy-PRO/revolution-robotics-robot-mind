# SPDX-License-Identifier: GPL-3.0-only


class Motors:
    RevvyMotor = {
        'driver': 'DcMotor',
        'config': {
            'speed_controller': [1 / 18, 0.5, 0, -200, 200],
            'position_controller': [4, 0, 0, -600, 600],
            'acceleration_limits': [14400, 3600],
            'encoder_resolution': 1536
        }
    }
    RevvyMotor_CCW = {
        'driver': 'DcMotor',
        'config': {
            'speed_controller': [1 / 18, 0.5, 0, -200, 200],
            'position_controller': [4, 0, 0, -600, 600],
            'acceleration_limits': [14400, 3600],
            'encoder_resolution': -1536
        }
    }


class Sensors:
    HC_SR04 = {'driver': 'HC_SR04', 'config': {}}
    BumperSwitch = {'driver': 'BumperSwitch', 'config': {}}
    EV3 = {'driver': 'EV3', 'config': {}}
    EV3_Color = {'driver': 'EV3_Color', 'config': {}}

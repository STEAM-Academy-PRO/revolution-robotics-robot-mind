# SPDX-License-Identifier: GPL-3.0-only


class Motors:
    RevvyMotor = {
        'driver': 'DcMotor',
        'config': {
            'speed_controller': [0.6065, 0.3935, 0, -150, 150],
            'position_controller': [0.1, 0.0000, 0, -150, 150],
            'acceleration_limits': [500, 500],
            'max_current': 1.5,
            'linearity': {5.0154: 18, 37.0370: 60, 67.7083: 100, 97.4151: 140, 144.0972: 200},
            'encoder_resolution': 12,
            'gear_ratio': 64.8
        }
    }
    RevvyMotor_CCW = {
        'driver': 'DcMotor',
        'config': {
            'speed_controller': [0.6065, 0.3935, 0, -150, 150],
            'position_controller': [0.1, 0.0000, 0, -150, 150],
            'acceleration_limits': [500, 500],
            'max_current': 1.5,
            'linearity': {5.0154: 18, 37.0370: 60, 67.7083: 100, 97.4151: 140, 144.0972: 200},
            'encoder_resolution': -12,
            'gear_ratio': 64.8
        }
    }


class Sensors:
    HC_SR04 = {'driver': 'HC_SR04', 'config': {}}
    BumperSwitch = {'driver': 'BumperSwitch', 'config': {}}
    EV3 = {'driver': 'EV3', 'config': {}}
    EV3_Color = {'driver': 'EV3_Color', 'config': {}}

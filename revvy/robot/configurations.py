# SPDX-License-Identifier: GPL-3.0-only


class Motors:
    RevvyMotor = {
        'driver': 'DcMotor',
        'config': {
            'speed_controller': [0.6065, 0.3935, 0, -150, 150],
            'position_controller': [0.1, 0.0000, 0, -150, 150],
            'acceleration_limits': [500, 500],
            'max_current': 1.5,
            'linearity': {4.6875: 16, 6.3477: 18, 7.8125: 20, 38.2813: 60, 99.3164: 100, 146.1914: 140},
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
            'linearity': {4.6875: 16, 6.3477: 18, 7.8125: 20, 38.2813: 60, 99.3164: 100, 146.1914: 140},
            'encoder_resolution': -12,
            'gear_ratio': 64.8
        }
    }


class Sensors:
    HC_SR04 = {'driver': 'HC_SR04', 'config': {}}
    BumperSwitch = {'driver': 'BumperSwitch', 'config': {}}
    EV3 = {'driver': 'EV3', 'config': {}}
    EV3_Color = {'driver': 'EV3_Color', 'config': {}}

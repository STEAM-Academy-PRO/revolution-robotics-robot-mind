# SPDX-License-Identifier: GPL-3.0-only

import collections
import struct

Orientation3D = collections.namedtuple('Orientation3D', ['pitch', 'roll', 'yaw'])

class IMU:
    def __init__(self):
        self._orientation = Orientation3D(0, 0, 0)

    @property
    def orientation(self):
        return self._orientation

    def update_gyro_data(self, data):
        (pitch, roll, yaw) = struct.unpack('<fff', data)
        self._orientation = Orientation3D(pitch, roll, yaw)

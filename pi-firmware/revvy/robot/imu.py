""" Inertial Measurement Unit: gyro and accelerometer """
import collections
import struct

Vector3D = collections.namedtuple('Vector3D', ['x', 'y', 'z'])
Orientation3D = collections.namedtuple('Orientation3D', ['pitch', 'roll', 'yaw'])


class IMU:
    def __init__(self):
        self._acceleration = Vector3D(0, 0, 0)
        self._rotation = Vector3D(0, 0, 0)
        self._orientation = Orientation3D(0, 0, 0)
        self._yaw_angle = 0
        self._relative_yaw_angle = 0

    @property
    def yaw_angle(self):
        return self._yaw_angle

    @property
    def relative_yaw_angle(self):
        return self._relative_yaw_angle  # TODO pinning is not yet implemented

    @property
    def acceleration(self):
        return self._acceleration

    @property
    def rotation(self):
        return self._rotation

    @property
    def orientation(self):
        return self._orientation

    @staticmethod
    def _read_vector(data, lsb_value):
        (x, y, z) = struct.unpack('<hhh', data)
        return Vector3D(x * lsb_value, y * lsb_value, z * lsb_value)

    def update_yaw_angles(self, data):
        (self._yaw_angle, self._relative_yaw_angle) = struct.unpack('<ll', data)
        # print('update_yaw_angles', data)

    def update_axl_data(self, data):
        """ LSM6DS3H sensor configuration constants """
        self._acceleration = self._read_vector(data, 0.061)
        # print('update_axl_data', data, self._acceleration)

    def update_gyro_data(self, data):
        """ LSM6DS3H sensor configuration constants """
        self._rotation = self._read_vector(data, 0.035*1.03)
        # print('update_gyro_data', data, self._rotation)

    def update_orientation_data(self, data):
        values = struct.unpack('<fff', data)
        self._orientation = Orientation3D(*values)
        # print('update_orientation_data', values)


""" Inertial Measurement Unit: gyro and accelerometer """

import struct
from typing import NamedTuple


class Vector3D(NamedTuple):
    x: float
    y: float
    z: float

    @staticmethod
    def deserialize(data):
        return Vector3D(*struct.unpack("<hhh", data))

    def __mul__(self, value) -> "Vector3D":
        return Vector3D(self.x * value, self.y * value, self.z * value)

    __rmul__ = __mul__


class Orientation3D(NamedTuple):
    pitch: float
    roll: float
    yaw: float

    @staticmethod
    def deserialize(data):
        return Orientation3D(*struct.unpack("<fff", data))


class IMU:
    def __init__(self) -> None:
        # raw sensor data
        self._acceleration = Vector3D(0, 0, 0)
        self._rotation = Vector3D(0, 0, 0)

        # processed data
        self._orientation = Orientation3D(0, 0, 0)
        self._yaw_angle = 0
        self._relative_yaw_angle = 0

    @property
    def yaw_angle(self) -> float:
        return self._yaw_angle

    @property
    def relative_yaw_angle(self) -> float:
        # TODO pinning (resetting the origin angle) is not yet implemented
        return self._relative_yaw_angle

    @property
    def acceleration(self) -> Vector3D:
        return self._acceleration

    @property
    def rotation(self) -> Vector3D:
        return self._rotation

    @property
    def orientation(self) -> Orientation3D:
        return self._orientation

    def update_yaw_angles(self, data: bytes):
        (self._yaw_angle, self._relative_yaw_angle) = struct.unpack("<ll", data)
        # print('update_yaw_angles', data)

    def update_axl_data(self, data: bytes):
        # LSM6DS3H sensor configuration constants
        self._acceleration = 0.061 * Vector3D.deserialize(data)
        # print('update_axl_data', data, self._acceleration)

    def update_gyro_data(self, data: bytes):
        # LSM6DS3H sensor configuration constants
        self._rotation = 0.035 * 1.03 * Vector3D.deserialize(data)
        # print('update_gyro_data', data, self._rotation)

    def update_orientation_data(self, data: bytes):
        self._orientation = Orientation3D.deserialize(data)
        # print('update_orientation_data', values)

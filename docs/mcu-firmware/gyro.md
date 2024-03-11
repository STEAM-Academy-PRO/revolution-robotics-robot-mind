Determining 3D orientation
==========================

Hardware, input data
--------------------

The intertial measurement unit we use is a [LSM6DS3H](../assets/LSM6DS3H.pdf) 6-DoF IMU. The chip
is configured for `±2g` acceleration (`0.061mg/LSB`) and `±1000°/s` angular velocity (`35mdps/LSB`)
measurement range. The sensor provides data with `416Hz` data rate.

The device driver is implemented in the `IMU` component. The component outputs data in physical
units and the following conventions:

| Axis           | Direction                        |
| -------------- | -------------------------------- |
| X acceleration | From R logo towards M1           |
| Y acceleration | From R logo towards sensor ports |
| Z acceleration | Outward from the R logo          |
| X rotation     | Around the X acceleration axis   |
| Y rotation     | Around the Y acceleration axis   |
| Z rotation     | Around the Z acceleration axis   |

Rotations are around their respective axis (e.g. X rotation is around the X acceleration axis)
according to the right hand rule: thumb points towards positive acceleration, fingers point
towards positive rotation.

Signal processing
-----------------

```
┌───┐   Raw acceleration + rotation
│IMU├─────────┬──────────────────────────────┬──────────────────────────┐
└───┘         │Raw rotation                  │Raw rotation              │Raw acceleration
       ┌──────▼─────────┐             ┌──────▼──────────┐         ┌─────▼──────────────┐
       │MovementDetector├────────────►│OffsetCompensator├────────►│OrientationEstimator│
       └────────────────┘ Is moving?  └─────────────────┘ Rotation└────────────────────┘
```

The gyroscope is prone to drifting and the amount of drift is not predictable and differs after
movement. To combat this, we define some arbitrary thresholding to detect when the Brain is not in
motion (`IMUMovementDetector`), then measure and subtract the drift if the Brian is not in motion
(`GyroscopeOffsetCompensator`). This compensation assumes the drift to be constant while the Brain
is in rest.

### Motion detection

In `IMUMovementDetector` we assume that physical motion has a certain noisiness. The component
assumes the Brain to be in rest if in the last 200 samples, all samples are within a `4°/s` window.
Similarly, if a sample is outside of this window, the Brain is assumed to be in motion and the
detection is reset around this value.

> FIXME: This algorithm does not handle slowly changing drift values perfectly:
> If the drift slowly, but monotonically, changes the component will periodically report the Brain
> to be in motion.

### Offset measurement and compensation

The `GyroscopeOffsetCompensator` measures an average drift value, then subtracts this drift from
the raw measurements. If the Brain is in motion, the averaging step is disabled. If the brain is
not in motion, the component collects 1000 samples, averages them, uses this average as the
drift value and resets sample collection.

> FIXME: The component starts outputting data only after determining the first average. This means that
> powering on the Brain on a rotating platform may never provide a rotation output.

> FIXME: The component tries to save memory by not implementing a proper siding window. However, the 2.5
> second measurement delay may be too long to introduce errors.

### Orientation estimation

The `IMUOrientationEstimator` component implements [Madgwick's algorithm](https://ahrs.readthedocs.io/en/latest/filters/madgwick.html#orientation-from-imu) to estimate orientations from the acceleration and angular speed
inputs.

> FIXME: We need to make sure we don't mix up our frames of reference in this component.
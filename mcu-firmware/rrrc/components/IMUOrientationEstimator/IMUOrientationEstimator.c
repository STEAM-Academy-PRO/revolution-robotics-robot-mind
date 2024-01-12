#include "IMUOrientationEstimator.h"
#include "utils.h"
#include "utils_assert.h"

/* Begin User Code Section: Declarations */
#include <math.h>

static Quaternion_t orientation;

static int32_t nTurns;
static float lastYaw;

static inline float deg_to_rad(float angle)
{
    return angle * (float)M_PI / 180.0f;
}

static inline float rad_to_deg(float rad)
{
    return rad * 180.0f / (float)M_PI;
}

static bool is_vector_empty(const Vector3D_t *v)
{
    return v->x == 0.0f && v->y == 0.0f && v->z == 0.0f;
}

/**
 * Constrains an angle given in the interval of [-2pi; 2pi] between [-pi; pi].
 */
static float constrain_angle(const float angle)
{
    if (angle < (float) -M_PI)
    {
        return 2.0f * (float) M_PI + angle;
    }
    else if (angle > (float) M_PI)
    {
        return -2.0f * (float) M_PI + angle;
    }
    else
    {
        return angle;
    }
}

static Orientation3D_t to_euler_angles(const Quaternion_t orientation)
{
    Orientation3D_t angles;

    float w = orientation.q0;
    float x = orientation.q1;
    float y = orientation.q2;
    float z = orientation.q3;

    // Algorithm adapted from: http://euclideanspace.com/maths/geometry/rotations/conversions/quaternionToEuler/index.htm
    // conventions:
    // * z is the vertical axis
    // * heading is about z
    // * roll is about x
    // * pitch is about y
    float test = z * x - w * y; // this is basically attitude
    const float vertical_threshold = 0.49f;
    if (test > vertical_threshold)
    {
        angles.yaw = constrain_angle(-2.0f * atan2f(-z, w));
        angles.pitch = M_PI_2;
        angles.roll = 0.0f;
    }
    else if (test < -vertical_threshold)
    {
        angles.yaw = constrain_angle(2.0f * atan2f(-z, w));
        angles.pitch = -M_PI_2;
        angles.roll = 0.0f;
    }
    else
    {
        float sqx = x * x;
        float sqy = y * y;
        float sqz = z * z;

        // roll (x-axis rotation)
        float sinr_cosp = 2.0f * (w * x + y * z);
        float cosr_cosp = 1.0f - 2.0f * (sqx + sqy);
        angles.roll = atan2f(sinr_cosp, cosr_cosp);

        // pitch (y-axis rotation)
        float sinp = 2.0f * test;
        angles.pitch = asinf(sinp);

        // yaw (z-axis rotation)
        float siny_cosp = 2.0f * (w * z + x * y);
        float cosy_cosp = 1.0f - 2.0f * (sqy + sqz);
        angles.yaw = atan2f(siny_cosp, cosy_cosp);
    }

    return angles;
}

static Quaternion_t madgwick_imu(const float sampleTime, const Vector3D_t acceleration, const Vector3D_t angularSpeed, const Quaternion_t previous)
{
    float q0 = previous.q0;
    float q1 = previous.q1;
    float q2 = previous.q2;
    float q3 = previous.q3;

    // Normalise accelerometer measurement
    float invLength = 1.0f / sqrtf(acceleration.x * acceleration.x + acceleration.y * acceleration.y + acceleration.z * acceleration.z);
    float x = acceleration.x * invLength;
    float y = acceleration.y * invLength;
    float z = acceleration.z * invLength;

    // Gradient descent algorithm corrective step
    float s0 = 2.0f * (2.0f * q0 * q2 * q2 + q2 * x + 2.0f * q0 * q1 * q1 - q1 * y);
    float s1 = 2.0f * (2.0f * q1 * q3 * q3 - q3 * x + 2.0f * q1 * q0 * q0 - q0 * y - 2.0f * q1 + 4.0f * q1 * q1 * q1 + 4.0f * q1 * q2 * q2 + 2.0f * q1 * z);
    float s2 = 2.0f * (2.0f * q0 * q0 * q2 + q0 * x + 2.0f * q2 * q3 * q3 - q3 * y - 2.0f * q2 + 4.0f * q2 * q1 * q1 + 4.0f * q2 * q2 * q2 + 2.0f * q2 * z);
    float s3 = 2.0f * (2.0f * q1 * q1 * q3 - q1 * x + 2.0f * q2 * q2 * q3 - q2 * y);

    // Apply feedback step
    const float beta = 1.0f; // < TODO: tune if necessary
    float scaling = beta / sqrtf(s0 * s0 + s1 * s1 + s2 * s2 + s3 * s3);

    // Rate of change of quaternion from gyroscope
    float qDot1 = 0.5f * (-q1 * angularSpeed.x - q2 * angularSpeed.y - q3 * angularSpeed.z) - s0 * scaling;
    float qDot2 = 0.5f * (q0 * angularSpeed.x + q2 * angularSpeed.z - q3 * angularSpeed.y) - s1 * scaling;
    float qDot3 = 0.5f * (q0 * angularSpeed.y - q1 * angularSpeed.z + q3 * angularSpeed.x) - s2 * scaling;
    float qDot4 = 0.5f * (q0 * angularSpeed.z + q1 * angularSpeed.y - q2 * angularSpeed.x) - s3 * scaling;

    // Integrate rate of change of quaternion to yield quaternion
    q0 += qDot1 * sampleTime;
    q1 += qDot2 * sampleTime;
    q2 += qDot3 * sampleTime;
    q3 += qDot4 * sampleTime;

    // Normalise quaternion
    float norm = 1.0f / sqrtf(q0 * q0 + q1 * q1 + q2 * q2 + q3 * q3);
    return (Quaternion_t){
        q0 * norm,
        q1 * norm,
        q2 * norm,
        q3 * norm,
    };
}

/* End User Code Section: Declarations */

void IMUOrientationEstimator_Run_OnInit(void)
{
    /* Begin User Code Section: OnInit:run Start */
    orientation = (Quaternion_t){1.0f, 0.0f, 0.0f, 0.0f};

    Orientation3D_t euler = to_euler_angles(orientation);
    IMUOrientationEstimator_Write_OrientationEuler(&euler);

    Vector3D_t vector;
    while (IMUOrientationEstimator_Read_Acceleration(&vector) != QueueStatus_Empty)
        ;

    while (IMUOrientationEstimator_Read_AngularSpeeds(&vector) != QueueStatus_Empty)
        ;

    nTurns = 0;
    lastYaw = 0.0f;
    /* End User Code Section: OnInit:run Start */
    /* Begin User Code Section: OnInit:run End */

    /* End User Code Section: OnInit:run End */
}

void IMUOrientationEstimator_Run_OnUpdate(void)
{
    /* Begin User Code Section: OnUpdate:run Start */
    Vector3D_t acceleration;
    const float sampleTime = IMUOrientationEstimator_Read_SampleTime();
    while (IMUOrientationEstimator_Read_Acceleration(&acceleration) != QueueStatus_Empty)
    {
        Vector3D_t angularSpeed;
        if (IMUOrientationEstimator_Read_AngularSpeeds(&angularSpeed) != QueueStatus_Empty)
        {
            if (is_vector_empty(&acceleration))
            {
                continue;
            }
            Vector3D_t angularSpeedRad = {
                .x = deg_to_rad(angularSpeed.x),
                .y = deg_to_rad(angularSpeed.y),
                .z = deg_to_rad(angularSpeed.z),
            };
            orientation = madgwick_imu(sampleTime, acceleration, angularSpeedRad, orientation);

            IMUOrientationEstimator_Write_Orientation(&orientation);

            const Orientation3D_t euler = to_euler_angles(orientation);
            IMUOrientationEstimator_Write_OrientationEuler(&euler);

            /* track yaw angle past the 360° mark */
            float yaw = rad_to_deg(euler.yaw);

            /*
             * yaw is the current rotation around the vertical (Z) axis
             * positive yaw, dYaw, nTurns: counterclockwise rotation
             * orientation estimation returns values between [-180, 180] (inclusive?)
             * the difference between angles is only expected to jump a half turn if it overflows
             * sign of dYaw indicates direction of rotation (current > last => positive => CCW)
             * dYaw > 180 -> assume current value underflowed while rotating CW (!) -> -1 turns
             */
            float dYaw = yaw - lastYaw;
            if (dYaw > 180.0f)
            {
                nTurns -= 1;
            }
            else if (dYaw < -180.0f)
            {
                nTurns += 1;
            }

            lastYaw = yaw;

            const Orientation3D_t eulerDegrees = {
                .pitch = rad_to_deg(euler.pitch),
                .roll = rad_to_deg(euler.roll),
                .yaw = yaw + nTurns * 360.0f,
            };
            IMUOrientationEstimator_Write_OrientationEulerDegrees(&eulerDegrees);
        }
    }
    /* End User Code Section: OnUpdate:run Start */
    /* Begin User Code Section: OnUpdate:run End */

    /* End User Code Section: OnUpdate:run End */
}

void IMUOrientationEstimator_Reset(void)
{
    orientation = (Quaternion_t) {1.0f, 0.0f, 0.0f, 0.0f };
}

__attribute__((weak))
void IMUOrientationEstimator_Write_Orientation(const Quaternion_t* value)
{
    ASSERT(value != NULL);
    /* Begin User Code Section: Orientation:write Start */

    /* End User Code Section: Orientation:write Start */
    /* Begin User Code Section: Orientation:write End */

    /* End User Code Section: Orientation:write End */
}

__attribute__((weak))
void IMUOrientationEstimator_Write_OrientationEuler(const Orientation3D_t* value)
{
    ASSERT(value != NULL);
    /* Begin User Code Section: OrientationEuler:write Start */

    /* End User Code Section: OrientationEuler:write Start */
    /* Begin User Code Section: OrientationEuler:write End */

    /* End User Code Section: OrientationEuler:write End */
}

__attribute__((weak))
void IMUOrientationEstimator_Write_OrientationEulerDegrees(const Orientation3D_t* value)
{
    ASSERT(value != NULL);
    /* Begin User Code Section: OrientationEulerDegrees:write Start */

    /* End User Code Section: OrientationEulerDegrees:write Start */
    /* Begin User Code Section: OrientationEulerDegrees:write End */

    /* End User Code Section: OrientationEulerDegrees:write End */
}

__attribute__((weak))
QueueStatus_t IMUOrientationEstimator_Read_Acceleration(Vector3D_t* value)
{
    ASSERT(value != NULL);
    /* Begin User Code Section: Acceleration:read Start */

    /* End User Code Section: Acceleration:read Start */
    /* Begin User Code Section: Acceleration:read End */

    /* End User Code Section: Acceleration:read End */
    return QueueStatus_Empty;
}

__attribute__((weak))
QueueStatus_t IMUOrientationEstimator_Read_AngularSpeeds(Vector3D_t* value)
{
    ASSERT(value != NULL);
    /* Begin User Code Section: AngularSpeeds:read Start */

    /* End User Code Section: AngularSpeeds:read Start */
    /* Begin User Code Section: AngularSpeeds:read End */

    /* End User Code Section: AngularSpeeds:read End */
    return QueueStatus_Empty;
}

__attribute__((weak))
float IMUOrientationEstimator_Read_SampleTime(void)
{
    /* Begin User Code Section: SampleTime:read Start */

    /* End User Code Section: SampleTime:read Start */
    /* Begin User Code Section: SampleTime:read End */

    /* End User Code Section: SampleTime:read End */
    return 0.0f;
}

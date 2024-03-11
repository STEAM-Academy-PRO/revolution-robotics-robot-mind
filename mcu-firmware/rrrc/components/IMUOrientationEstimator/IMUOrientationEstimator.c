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

static inline Vector3D_t vec3d_mult_scalar(const Vector3D_t v, const float scalar)
{
    return (Vector3D_t) {
        .x = v.x * scalar,
        .y = v.y * scalar,
        .z = v.z * scalar,
    };
}

static inline Vector3D_t vec3d_norm(const Vector3D_t v)
{
    float norm = 1.0f / sqrtf(v.x * v.x + v.y * v.y + v.z * v.z);
    return vec3d_mult_scalar(v, norm);
}

static inline Quaternion_t q_add(const Quaternion_t q, const Quaternion_t r)
{
    return (Quaternion_t) {
        .q0 = q.q0 + r.q0,
        .q1 = q.q1 + r.q1,
        .q2 = q.q2 + r.q2,
        .q3 = q.q3 + r.q3,
    };
}

static inline Quaternion_t q_sub(const Quaternion_t q, const Quaternion_t r)
{
    return (Quaternion_t) {
        .q0 = q.q0 - r.q0,
        .q1 = q.q1 - r.q1,
        .q2 = q.q2 - r.q2,
        .q3 = q.q3 - r.q3,
    };
}

static inline Quaternion_t q_mult_scalar(const Quaternion_t q, const float scalar)
{
    return (Quaternion_t) {
        .q0 = q.q0 * scalar,
        .q1 = q.q1 * scalar,
        .q2 = q.q2 * scalar,
        .q3 = q.q3 * scalar,
    };
}

static inline Quaternion_t q_norm(const Quaternion_t q)
{
    float norm = 1.0f / sqrtf(q.q0 * q.q0 + q.q1 * q.q1 + q.q2 * q.q2 + q.q3 * q.q3);

    return q_mult_scalar(q, norm);
}

/**
 * Multiplies two quaternions using the Hamilton product.
 */
static inline Quaternion_t q_mult(const Quaternion_t q, const Quaternion_t r)
{
    return (Quaternion_t) {
        .q0 = q.q0 * r.q0 - q.q1 * r.q1 - q.q2 * r.q2 - q.q3 * r.q3,
        .q1 = q.q0 * r.q1 + q.q1 * r.q0 + q.q2 * r.q3 - q.q3 * r.q2,
        .q2 = q.q0 * r.q2 - q.q1 * r.q3 + q.q2 * r.q0 + q.q3 * r.q1,
        .q3 = q.q0 * r.q3 + q.q1 * r.q2 - q.q2 * r.q1 + q.q3 * r.q0,
    };
}

/**
 * A straight implementation of https://ahrs.readthedocs.io/en/latest/filters/madgwick.html#ahrs.filters.madgwick.Madgwick.updateIMU
 *
 * @param sampleTime the time between two consecutive measurements in seconds
 * @param acceleration the acceleration vector in m/s^2
 * @param angularSpeed the angular speed vector in rad/s
 * @param previous the previous orientation quaternion
 * @return the updated orientation quaternion
 */
static Quaternion_t madgwick_imu(const float sampleTime, const Vector3D_t acceleration, const Vector3D_t angularSpeed, const Quaternion_t previous)
{
    const float beta = 1.0f; // < gyroscipe gain TODO: tune if necessary

    // Rename to shorten expressions
    Quaternion_t q = previous;
    Vector3D_t g = angularSpeed;

    // Normalise accelerometer measurement
    Vector3D_t a = vec3d_norm(acceleration);

    // Gradient descent algorithm corrective step
    // fg(q, sa)
    float fg[3] = {
        2.0f * (q.q1 * q.q3 - q.q0 * q.q2) - a.x,
        2.0f * (q.q0 * q.q1 + q.q2 * q.q3) - a.y,
        2.0f * (0.5f - q.q1 * q.q1 - q.q2 * q.q2) - a.z
    };
    // Jg(q)
    float jg[3][4] = {
        { -2.0f * q.q2, 2.0f * q.q3, -2.0f * q.q0, 2.0f * q.q1 },
        {  2.0f * q.q1, 2.0f * q.q0,  2.0f * q.q3, 2.0f * q.q2 },
        {  0.0f,       -4.0f * q.q1, -4.0f * q.q2, 0.0f }
    };
    // step = Jg(q)^T * fg(q, sa)
    Quaternion_t step = (Quaternion_t) {
        .q0 = 0.0,
        .q1 = 0.0,
        .q2 = 0.0,
        .q3 = 0.0,
    };
    for (int i = 0; i < 3; i++)
    {
        step.q0 += jg[i][0] * fg[i];
        step.q1 += jg[i][1] * fg[i];
        step.q2 += jg[i][2] * fg[i];
        step.q3 += jg[i][3] * fg[i];
    }

    // Rate of change of quaternion from gyroscope
    // qwDot(t) = 0.5 * q(t) * (0, gx, gy, gz)
    Quaternion_t qwDot = q_mult_scalar(
        q_mult(
            q,
            (Quaternion_t) {
                .q0 = 0.0f,
                .q1 = g.x,
                .q2 = g.y,
                .q3 = g.z,
            }
        ),
        0.5f
    );

    // qDot(t) = qwDot(t) - beta * step(t) / ||step(t)||
    Quaternion_t qDot = q_sub(qwDot, q_mult_scalar(q_norm(step), beta));

    // Integrate rate of change of quaternion
    // q(t) = q(t-1) + qDot(t) * dt
    Quaternion_t qOut = q_add(
        previous,
        q_mult_scalar(
            qDot,
            sampleTime
        )
    );

    return q_norm(qOut);
}

static void UpdateOrientationResult(const Quaternion_t result)
{
    orientation = result;
    IMUOrientationEstimator_Write_Orientation(&orientation);

    Orientation3D_t euler = to_euler_angles(orientation);
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

void IMUOrientationEstimator_Reset(void)
{
    nTurns = 0;
    lastYaw = 0.0f;

    UpdateOrientationResult((Quaternion_t) { 1.0f, 0.0f, 0.0f, 0.0f });
}
/* End User Code Section: Declarations */

void IMUOrientationEstimator_Run_OnInit(void)
{
    /* Begin User Code Section: OnInit:run Start */
    IMUOrientationEstimator_Reset();

    Vector3D_t vector;
    while (IMUOrientationEstimator_Read_Acceleration(&vector) != QueueStatus_Empty)
        ;

    while (IMUOrientationEstimator_Read_AngularSpeeds(&vector) != QueueStatus_Empty)
        ;
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
            Quaternion_t result = madgwick_imu(sampleTime, acceleration, angularSpeedRad, orientation);
            UpdateOrientationResult(result);
        }
    }
    /* End User Code Section: OnUpdate:run Start */
    /* Begin User Code Section: OnUpdate:run End */

    /* End User Code Section: OnUpdate:run End */
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

#ifndef COMPONENT_IMU_ORIENTATION_ESTIMATOR_H_
#define COMPONENT_IMU_ORIENTATION_ESTIMATOR_H_

#ifndef COMPONENT_TYPES_IMU_ORIENTATION_ESTIMATOR_H_
#define COMPONENT_TYPES_IMU_ORIENTATION_ESTIMATOR_H_

#include <float.h>


typedef struct {
    float x;
    float y;
    float z;
} Vector3D_t;

typedef struct {
    float pitch;
    float roll;
    float yaw;
} Orientation3D_t;

typedef struct {
    float q0;
    float q1;
    float q2;
    float q3;
} Quaternion_t;

typedef enum {
    QueueStatus_Empty,
    QueueStatus_Ok,
    QueueStatus_Overflow
} QueueStatus_t;

#endif /* COMPONENT_TYPES_IMU_ORIENTATION_ESTIMATOR_H_ */

void IMUOrientationEstimator_Run_OnInit(void);
void IMUOrientationEstimator_Run_OnUpdate(void);
void IMUOrientationEstimator_Write_Orientation(const Quaternion_t* value);
void IMUOrientationEstimator_Write_OrientationEuler(const Orientation3D_t* value);
void IMUOrientationEstimator_Write_OrientationEulerDegrees(const Orientation3D_t* value);
QueueStatus_t IMUOrientationEstimator_Read_Acceleration(Vector3D_t* value);
QueueStatus_t IMUOrientationEstimator_Read_AngularSpeeds(Vector3D_t* value);
float IMUOrientationEstimator_Read_SampleTime(void);
void IMUOrientationEstimator_Reset(void);

#endif /* COMPONENT_IMU_ORIENTATION_ESTIMATOR_H_ */

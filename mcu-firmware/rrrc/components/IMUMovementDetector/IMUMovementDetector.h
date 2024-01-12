#ifndef COMPONENT_IMU_MOVEMENT_DETECTOR_H_
#define COMPONENT_IMU_MOVEMENT_DETECTOR_H_

#ifndef COMPONENT_TYPES_IMU_MOVEMENT_DETECTOR_H_
#define COMPONENT_TYPES_IMU_MOVEMENT_DETECTOR_H_

#include <float.h>
#include <stdbool.h>


typedef struct {
    float x;
    float y;
    float z;
} Vector3D_t;

typedef enum {
    QueueStatus_Empty,
    QueueStatus_Ok,
    QueueStatus_Overflow
} QueueStatus_t;

#endif /* COMPONENT_TYPES_IMU_MOVEMENT_DETECTOR_H_ */

void IMUMovementDetector_Run_OnInit(void);
void IMUMovementDetector_Run_OnUpdate(void);
void IMUMovementDetector_Write_IsMoving(bool value);
QueueStatus_t IMUMovementDetector_Read_Acceleration(Vector3D_t* value);
QueueStatus_t IMUMovementDetector_Read_AngularSpeeds(Vector3D_t* value);

#endif /* COMPONENT_IMU_MOVEMENT_DETECTOR_H_ */

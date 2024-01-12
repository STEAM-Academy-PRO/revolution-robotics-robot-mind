#ifndef COMPONENT_IMU_H_
#define COMPONENT_IMU_H_

#ifndef COMPONENT_TYPES_IMU_H_
#define COMPONENT_TYPES_IMU_H_

#include "components/ErrorStorage/ErrorStorageTypes.h"
#include <float.h>
#include <stdint.h>


typedef struct {
    int16_t x;
    int16_t y;
    int16_t z;
} IMU_RawSample_t;

typedef struct {
    float x;
    float y;
    float z;
} Vector3D_t;

#endif /* COMPONENT_TYPES_IMU_H_ */

void IMU_Run_OnInit(void);
void IMU_Run_OnUpdate(void);
float IMU_Constant_SampleTime(void);
void IMU_Call_LogError(const ErrorInfo_t* data);
void IMU_Write_AccelerometerSample(const Vector3D_t* value);
void IMU_Write_GyroscopeSample(const Vector3D_t* value);
void IMU_Write_RawAccelerometerSample(const IMU_RawSample_t* value);
void IMU_Write_RawGyroscopeSample(const IMU_RawSample_t* value);

#endif /* COMPONENT_IMU_H_ */

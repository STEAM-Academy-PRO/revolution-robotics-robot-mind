#ifndef COMPONENT_MOTOR_DERATING_H_
#define COMPONENT_MOTOR_DERATING_H_

#ifndef COMPONENT_TYPES_MOTOR_DERATING_H_
#define COMPONENT_TYPES_MOTOR_DERATING_H_

#include <float.h>
#include <stdint.h>

typedef float Temperature_t;
typedef float Percentage_t;
typedef float Current_t;

typedef struct {
    Temperature_t MaxSafeTemperature;
    Temperature_t MaxAllowedTemperature;
} MotorDeratingParameters_t;

#endif /* COMPONENT_TYPES_MOTOR_DERATING_H_ */

void MotorDerating_Run_OnUpdate(void);
void MotorDerating_Write_DeratedControlValue(uint32_t index, int16_t value);
void MotorDerating_Write_MaxPowerRatio(uint32_t index, Percentage_t value);
void MotorDerating_Write_RelativeMotorCurrent(uint32_t index, Percentage_t value);
int16_t MotorDerating_Read_ControlValue(uint32_t index);
Current_t MotorDerating_Read_MaxMotorCurrent(uint32_t index);
Current_t MotorDerating_Read_MotorCurrent(uint32_t index);
Temperature_t MotorDerating_Read_MotorTemperature(uint32_t index);
void MotorDerating_Read_Parameters(MotorDeratingParameters_t* value);

#endif /* COMPONENT_MOTOR_DERATING_H_ */

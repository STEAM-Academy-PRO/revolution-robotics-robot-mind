#ifndef COMPONENT_MOTOR_THERMAL_MODEL_H_
#define COMPONENT_MOTOR_THERMAL_MODEL_H_

#ifndef COMPONENT_TYPES_MOTOR_THERMAL_MODEL_H_
#define COMPONENT_TYPES_MOTOR_THERMAL_MODEL_H_

#include <float.h>
#include <stdint.h>

typedef float Current_t;
typedef float Temperature_t;

typedef struct {
    float resistance;
    float coeff_cooling;
    float coeff_heating;
} MotorThermalParameters_t;

#endif /* COMPONENT_TYPES_MOTOR_THERMAL_MODEL_H_ */

/* Begin User Code Section: Declarations */

/* End User Code Section: Declarations */

void MotorThermalModel_Run_OnInit(void);
void MotorThermalModel_Run_OnUpdate(void);
void MotorThermalModel_Write_Temperature(uint32_t index, Temperature_t value);
Temperature_t MotorThermalModel_Read_AmbientTemperature(void);
Current_t MotorThermalModel_Read_MotorCurrent(uint32_t index);
void MotorThermalModel_Read_ThermalParameters(MotorThermalParameters_t* value);

#endif /* COMPONENT_MOTOR_THERMAL_MODEL_H_ */

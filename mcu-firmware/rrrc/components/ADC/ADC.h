#ifndef COMPONENT_ADC_H_
#define COMPONENT_ADC_H_

#ifndef COMPONENT_TYPES_ADC_H_
#define COMPONENT_TYPES_ADC_H_

#include <float.h>
#include <stdint.h>

typedef float Voltage_t;
typedef float Current_t;

#endif /* COMPONENT_TYPES_ADC_H_ */

/* Begin User Code Section: Declarations */
#include <stdbool.h>

bool ADC_DetectMotorStart(int motor_idx, uint8_t threshold_delta);
void ADC_DetectMotorStop(void);
bool ADC_DetectMotorDetected(void);
/* End User Code Section: Declarations */

void ADC_Run_OnInit(void);
void ADC_Run_Update(void);
void ADC_RaiseEvent_InitDoneISR(void);
void ADC_Write_MainBatteryVoltage(Voltage_t value);
void ADC_Write_MotorBatteryVoltage(Voltage_t value);
void ADC_Write_MotorCurrent(uint32_t index, Current_t value);
void ADC_Write_Sensor_ADC(uint32_t index, uint8_t value);

#endif /* COMPONENT_ADC_H_ */

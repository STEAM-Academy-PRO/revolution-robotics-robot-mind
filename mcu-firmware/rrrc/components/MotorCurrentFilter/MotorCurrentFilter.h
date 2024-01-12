#ifndef COMPONENT_MOTOR_CURRENT_FILTER_H_
#define COMPONENT_MOTOR_CURRENT_FILTER_H_

#ifndef COMPONENT_TYPES_MOTOR_CURRENT_FILTER_H_
#define COMPONENT_TYPES_MOTOR_CURRENT_FILTER_H_

#include <float.h>
#include <stdint.h>

typedef float Current_t;

#endif /* COMPONENT_TYPES_MOTOR_CURRENT_FILTER_H_ */

void MotorCurrentFilter_Run_OnInit(void);
void MotorCurrentFilter_Run_Update(void);
void MotorCurrentFilter_Write_FilteredCurrent(uint32_t index, Current_t value);
Current_t MotorCurrentFilter_Read_RawCurrent(uint32_t index);

#endif /* COMPONENT_MOTOR_CURRENT_FILTER_H_ */

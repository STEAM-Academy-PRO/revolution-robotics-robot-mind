#ifndef MOTOR_PORT_HANDLER_INTERNAL_H_
#define MOTOR_PORT_HANDLER_INTERNAL_H_

#include "MotorPortHandler.h"

#include <stdbool.h>

void MotorPort_SetGreenLed(MotorPort_t* port, bool state);
void MotorPort_SetDriveValue(MotorPort_t* port, int16_t value);
void MotorPort_WriteMaxCurrent(MotorPort_t* port, Current_t value);
Percentage_t MotorPort_ReadCurrentPercentage(MotorPort_t* port);

void MotorPort_DisableExti0(MotorPort_t* motorPort);
void MotorPort_DisableExti1(MotorPort_t* motorPort);
void MotorPort_EnableExti0(MotorPort_t* motorPort);
void MotorPort_EnableExti1(MotorPort_t* motorPort);

bool MotorPort_Read_Enc0(MotorPort_t* port);
bool MotorPort_Read_Enc1(MotorPort_t* port);

#endif /* MOTOR_PORT_HANDLER_INTERNAL_H_ */

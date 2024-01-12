#ifndef SENSOR_PORT_HANDLER_INTERNAL_H_
#define SENSOR_PORT_HANDLER_INTERNAL_H_

#include "SensorPortHandler.h"

#include <hal_ext_irq.h>

typedef enum {
    Sensor_VccIo_3V3,
    Sensor_VccIo_5V
} Sensor_VccIo_t;

void SensorPort_SetGreenLed(struct _SensorPort_t* port, bool state);
void SensorPort_SetOrangeLed(struct _SensorPort_t* port, bool state);

void SensorPort_ToggleGreenLed(struct _SensorPort_t* port);
void SensorPort_ToggleOrangeLed(struct _SensorPort_t* port);

void SensorPort_ConfigureGpio0_Input(struct _SensorPort_t* port);
void SensorPort_ConfigureGpio0_Output(struct _SensorPort_t* port);

void SensorPort_ConfigureGpio1_Input(struct _SensorPort_t* port);
void SensorPort_ConfigureGpio1_Output(struct _SensorPort_t* port);
void SensorPort_ConfigureGpio1_Interrupt(struct _SensorPort_t* port);
void SensorPort_ConfigureGpio1_CustomInterrupt(struct _SensorPort_t* port,
    ext_irq_cb_t custom_interrupt_callback);
void SensorPort_ConfigureGpio1_ClearPendingInterrupt(struct _SensorPort_t* port);

bool SensorPort_Read_Gpio0(struct _SensorPort_t* port);
bool SensorPort_Read_Gpio1(struct _SensorPort_t* port);

void SensorPort_SetGpio0_Output(struct _SensorPort_t* port, bool state);
void SensorPort_SetGpio1_Output(struct _SensorPort_t* port, bool state);

void SensorPort_SetVccIo(struct _SensorPort_t* port, Sensor_VccIo_t voltage);

void SensorPort_ext1_callback(void* user_data);

#endif /* SENSOR_PORT_HANDLER_INTERNAL_H_ */

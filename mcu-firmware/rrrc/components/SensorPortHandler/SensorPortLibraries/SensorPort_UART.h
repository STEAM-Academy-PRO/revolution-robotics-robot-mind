#ifndef SENSOR_PORT_UART_H_
#define SENSOR_PORT_UART_H_

#include "hal/sercom/sercom_uart.h"

typedef enum {
    SensorPort_UART_Success,
    SensorPort_UART_Error
} SensorPort_UART_Status_t;

#include "../SensorPortHandlerInternal.h"

SensorPort_UART_Status_t SensorPort_UART_Enable(struct _SensorPort_t* port, uint32_t baudrate);
SensorPort_UART_Status_t SensorPort_UART_Disable(struct _SensorPort_t* port);
SensorPort_UART_Status_t SensorPort_UART_Receive(struct _SensorPort_t* port, UARTByteReceivedCallback_t callback);
SensorPort_UART_Status_t SensorPort_UART_Transmit(struct _SensorPort_t* port, const uint8_t* pData, size_t count, UARTTxCompleteCallback_t callback);

#endif /* SENSOR_PORT_UART_H_ */

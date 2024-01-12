#include "SensorPort_UART.h"
#include <hal_gpio.h>

SensorPort_UART_Status_t SensorPort_UART_Enable(SensorPort_t* port, uint32_t baudrate)
{
    ASSERT(port->interfaceType == SensorPortComm_None);

    UARTConfig_t config = {
        .hw = port->comm_hw,
        .baud_rate = baudrate
    };

    if (sercom_uart_init(&port->sercom.uart, &config) == UARTResult_Ok)
    {
        gpio_set_pin_pull_mode(port->comm_pin0.pin, GPIO_PULL_OFF);
        gpio_set_pin_pull_mode(port->comm_pin1.pin, GPIO_PULL_OFF);
        gpio_set_pin_function(port->comm_pin0.pin, port->comm_pin0.function); // TX
        gpio_set_pin_function(port->comm_pin1.pin, port->comm_pin1.function); // RX
        port->interfaceType = SensorPortComm_UART;
    
        return SensorPort_UART_Success;
    }
    else
    {
        return SensorPort_UART_Error;
    }
}

SensorPort_UART_Status_t SensorPort_UART_Disable(SensorPort_t* port)
{
    ASSERT(port->interfaceType == SensorPortComm_UART);

    gpio_set_pin_function(port->comm_pin0.pin, GPIO_PIN_FUNCTION_OFF);
    gpio_set_pin_function(port->comm_pin1.pin, GPIO_PIN_FUNCTION_OFF);

    sercom_uart_deinit(&port->sercom.uart);

    port->interfaceType = SensorPortComm_None;
    return SensorPort_UART_Success;
}

SensorPort_UART_Status_t SensorPort_UART_Receive(SensorPort_t* port, UARTByteReceivedCallback_t callback)
{
    ASSERT(port->interfaceType == SensorPortComm_UART);
    if (callback)
    {
        sercom_uart_start_reception(&port->sercom.uart, callback);
    }
    else
    {
        sercom_uart_stop_reception(&port->sercom.uart);
    }
    return SensorPort_UART_Success;
}

SensorPort_UART_Status_t SensorPort_UART_Transmit(SensorPort_t* port, const uint8_t* pData, size_t count, UARTTxCompleteCallback_t callback)
{
    ASSERT(port->interfaceType == SensorPortComm_UART);
    
    if (sercom_uart_write(&port->sercom.uart, pData, count, callback) == UARTResult_Ok)
    {
        return SensorPort_UART_Success;
    }
    else
    {
        return SensorPort_UART_Error;
    }
}

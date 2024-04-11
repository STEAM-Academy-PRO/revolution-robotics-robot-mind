#include "MotorPortHandlerInternal.h"
#include "MotorPortLibraries/MotorPortLibrary.h"

#include <hal_gpio.h>
#include <hal_ext_irq.h>

void MotorPort_SetGreenLed(MotorPort_t* port, bool state)
{
    gpio_set_pin_level(port->gpio.led, !state);
}

void MotorPort_SetDriveValue(MotorPort_t* port, int16_t value)
{
    MotorPortHandler_Write_DriveStrength(port->port_idx, value);
}

void MotorPort_WriteMaxCurrent(MotorPort_t* port, Current_t value)
{
    MotorPortHandler_Write_MaxAllowedCurrent(port->port_idx, value);
}

Percentage_t MotorPort_ReadCurrentPercentage(MotorPort_t* port)
{
    return MotorPortHandler_Read_RelativeMotorCurrent(port->port_idx);
}

bool MotorPort_Read_Enc0(MotorPort_t* port)
{
    return fast_gpio_read_pin(port->gpio.enc0) != 0u;
}

bool MotorPort_Read_Enc1(MotorPort_t* port)
{
    return fast_gpio_read_pin(port->gpio.enc1) != 0u;
}

void MotorPort_DisableExti0(MotorPort_t* motorPort)
{
    int32_t res = ext_irq_disable(GPIO_FROM_FAST_PIN(motorPort->gpio.enc0));
    ASSERT(res == ERR_NONE);
}

void MotorPort_DisableExti1(MotorPort_t* motorPort)
{
    int32_t res = ext_irq_disable(GPIO_FROM_FAST_PIN(motorPort->gpio.enc1));
    ASSERT(res == ERR_NONE);
}

void MotorPort_EnableExti0(MotorPort_t* motorPort)
{
    const MotorLibrary_t* library = motorPort->library;
    if (library->Gpio0Callback != NULL)
    {
        int32_t res = ext_irq_enable(GPIO_FROM_FAST_PIN(motorPort->gpio.enc0), library->Gpio0Callback, motorPort);
        ASSERT(res == ERR_NONE);
    }
}

void MotorPort_EnableExti1(MotorPort_t* motorPort)
{
    const MotorLibrary_t* library = motorPort->library;
    if (library->Gpio0Callback != NULL)
    {
        int32_t res = ext_irq_enable(GPIO_FROM_FAST_PIN(motorPort->gpio.enc1), library->Gpio1Callback, motorPort);
        ASSERT(res == ERR_NONE);
    }
}

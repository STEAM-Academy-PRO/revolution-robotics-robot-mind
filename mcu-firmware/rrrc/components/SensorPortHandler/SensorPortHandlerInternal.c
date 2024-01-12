/*
 * SensorPortHandlerInternal.c
 *
 * Created: 10/05/2019 18:01:33
 *  Author: D�niel Buga
 */ 
#include "SensorPortHandlerInternal.h"
#include "atmel_start_pins.h"

void SensorPort_SetGreenLed(SensorPort_t* port, bool state)
{
    gpio_set_pin_level(port->led0, !state);
}

void SensorPort_ToggleGreenLed(SensorPort_t* port)
{
    gpio_toggle_pin_level(port->led0);
}

void SensorPort_SetOrangeLed(SensorPort_t* port, bool state)
{
    gpio_set_pin_level(port->led1, !state);
}

void SensorPort_ToggleOrangeLed(SensorPort_t* port)
{
    gpio_toggle_pin_level(port->led1);
}

void SensorPort_ConfigureGpio0_Input(SensorPort_t* port)
{
    gpio_set_pin_pull_mode(port->gpio0, GPIO_PULL_OFF);
    gpio_set_pin_direction(port->gpio0, GPIO_DIRECTION_IN);
    gpio_set_pin_function(port->gpio0, GPIO_PIN_FUNCTION_OFF);
}

void SensorPort_ConfigureGpio0_Output(SensorPort_t* port)
{
    gpio_set_pin_pull_mode(port->gpio0, GPIO_PULL_OFF);
    gpio_set_pin_direction(port->gpio0, GPIO_DIRECTION_OUT);
    gpio_set_pin_function(port->gpio0, GPIO_PIN_FUNCTION_OFF);
    gpio_set_pin_level(port->gpio0, false);
}

void SensorPort_ConfigureGpio1_Input(SensorPort_t* port)
{
    gpio_set_pin_pull_mode(port->gpio1, GPIO_PULL_OFF);
    gpio_set_pin_direction(port->gpio1, GPIO_DIRECTION_IN);
    gpio_set_pin_function(port->gpio1, GPIO_PIN_FUNCTION_OFF);

    int32_t res = ext_irq_disable(port->gpio1);
    ASSERT(res == ERR_NONE);
}

void SensorPort_ConfigureGpio1_Output(SensorPort_t* port)
{
    gpio_set_pin_pull_mode(port->gpio1, GPIO_PULL_OFF);
    gpio_set_pin_direction(port->gpio1, GPIO_DIRECTION_OUT);
    gpio_set_pin_function(port->gpio1, GPIO_PIN_FUNCTION_OFF);
    gpio_set_pin_level(port->gpio1, false);

    int32_t res = ext_irq_disable(port->gpio1);
    ASSERT(res == ERR_NONE);
}

void SensorPort_ConfigureGpio1_CustomInterrupt(SensorPort_t* port,
    ext_irq_cb_t custom_interrupt_callback)
{
    gpio_set_pin_pull_mode(port->gpio1, GPIO_PULL_OFF);
    gpio_set_pin_direction(port->gpio1, GPIO_DIRECTION_IN);
    gpio_set_pin_function(port->gpio1, GPIO_PIN_FUNCTION_A);

    int32_t res = ext_irq_enable(port->gpio1, custom_interrupt_callback, port);
    ASSERT(res == ERR_NONE);
}

void SensorPort_ConfigureGpio1_ClearPendingInterrupt(SensorPort_t* port)
{
    ext_irq_clear_pending(port->gpio1);
}

void SensorPort_ConfigureGpio1_Interrupt(SensorPort_t* port)
{
    SensorPort_ConfigureGpio1_CustomInterrupt(port, SensorPort_ext1_callback);
}

bool SensorPort_Read_Gpio0(SensorPort_t* port)
{
    return gpio_get_pin_level(port->gpio0) != 0u;
}

bool SensorPort_Read_Gpio1(SensorPort_t* port)
{
    return gpio_get_pin_level(port->gpio1) != 0u;
}

void SensorPort_SetGpio0_Output(SensorPort_t* port, bool state)
{
    gpio_set_pin_level(port->gpio0, state);
}

void SensorPort_SetGpio1_Output(SensorPort_t* port, bool state)
{
    gpio_set_pin_level(port->gpio1, state);
}

void SensorPort_SetVccIo(SensorPort_t* port, Sensor_VccIo_t voltage)
{
    switch(voltage)
    {
        default:
        case Sensor_VccIo_3V3:
            gpio_set_pin_level(port->vccio, false);
            break;

        case Sensor_VccIo_5V:
            gpio_set_pin_level(port->vccio, true);
            break;
    }
}

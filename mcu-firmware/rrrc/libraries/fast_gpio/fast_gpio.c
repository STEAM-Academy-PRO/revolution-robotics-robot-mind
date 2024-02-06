#include "fast_gpio.h"

uint32_t fast_gpio_read_pin(fast_gpio_t pin)
{
    return pin.port_reg->IN.reg & pin.pin_mask;
}

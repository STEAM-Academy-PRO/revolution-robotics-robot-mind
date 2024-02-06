#ifndef HAL_FAST_GPIO_H_
#define HAL_FAST_GPIO_H_

#include <stdio.h>
#include <hal_gpio.h>

typedef struct {
    uint32_t port;
    uint32_t pin_mask;
    PortGroup* port_reg;
    uint8_t gpio;
} fast_gpio_t;

#define FAST_PIN(_port, _pin) {       \
    .port = _port,                    \
    .port_reg = &(PORT->Group[_port]),\
    .pin_mask = (1u << _pin),         \
    .gpio = GPIO(_port, _pin)         \
}

#define FAST_FROM_GPIO(_pin) FAST_PIN(GPIO_PORT(_pin), GPIO_PIN(_pin))

#define GPIO_FROM_FAST_PIN(_gpio) (_gpio).gpio

uint32_t fast_gpio_read_pin(fast_gpio_t pin);

#endif /* HAL_FAST_GPIO_H_ */

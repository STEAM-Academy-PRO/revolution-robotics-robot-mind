#ifndef DRIVER_INIT_INCLUDED
#define DRIVER_INIT_INCLUDED

#include "atmel_start_pins.h"

#ifdef __cplusplus
extern "C" {
#endif

#include <peripheral_clk_config.h>

#include <hal_atomic.h>
#include <hal_delay.h>
#include <hal_gpio.h>
#include <hal_init.h>
#include <hal_io.h>
#include <hal_sleep.h>

#include <hal_flash.h>

#include <hal_i2c_s_async.h>
#include <hal_spi_m_dma.h>
#include <hal_spi_m_sync.h>
#include <hpl_tc_base.h>

extern struct flash_descriptor FLASH_0;

/**
 * \brief Perform system initialization, initialize pins and clocks for
 * peripherals
 */
void system_init(void);

void watchdog_start(void);

#ifdef __cplusplus
}
#endif
#endif // DRIVER_INIT_INCLUDED

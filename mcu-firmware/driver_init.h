#ifndef DRIVER_INIT_INCLUDED
#define DRIVER_INIT_INCLUDED

#include "atmel_start_pins.h"

#include <hal_atomic.h>
#include <hal_delay.h>
#include <hal_gpio.h>
#include <hal_init.h>
#include <hal_io.h>
#include <hal_sleep.h>

#include <hal_ext_irq.h>
#include <hpl_tc_base.h>
#include <hal_delay.h>
#include <hal_wdt.h>

#include <hal_spi_m_dma.h>
#include <hal_spi_m_sync.h>

#include <tc_lite.h>

void system_init(void);

#endif // DRIVER_INIT_INCLUDED

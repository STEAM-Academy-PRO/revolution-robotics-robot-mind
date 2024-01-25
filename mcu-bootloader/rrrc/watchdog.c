#include "watchdog.h"

#include <compiler.h>
#include "hri_mclk_d51.h"
#include "hri_wdt_d51.h"

void watchdog_start(void)
{
    hri_mclk_set_APBAMASK_WDT_bit(MCLK);
    hri_wdt_clear_CTRLA_WEN_bit(WDT);
    hri_wdt_write_CONFIG_PER_bf(WDT, 0x07u);
    hri_wdt_set_CTRLA_ENABLE_bit(WDT);
}

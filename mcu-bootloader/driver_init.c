#include "driver_init.h"
#include <peripheral_clk_config.h>
#include <utils.h>
#include <hal_init.h>
#include "utils/crc.h"

struct flash_descriptor FLASH_0;

void FLASH_0_CLOCK_init(void)
{
    hri_mclk_set_AHBMASK_NVMCTRL_bit(MCLK);
}

void FLASH_0_init(void)
{
    FLASH_0_CLOCK_init();
    flash_init(&FLASH_0, NVMCTRL);
}

void system_init(void)
{
    // Perform the very basic init and check the bootloader mode request
    init_mcu();
    CRC32_Init();
    FLASH_0_init();
}

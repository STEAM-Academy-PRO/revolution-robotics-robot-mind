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

    // Temporarily (until next boot) write-protect the bootloader pages (first 64K for now)
    flash_lock(&FLASH_0, 0, 32);
    flash_lock(&FLASH_0, 0x4000, 32);
    flash_lock(&FLASH_0, 0x8000, 32);
    flash_lock(&FLASH_0, 0xC000, 32);
}

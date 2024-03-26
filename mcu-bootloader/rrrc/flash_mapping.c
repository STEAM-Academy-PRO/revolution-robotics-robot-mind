#include "libraries/crc.h"
#include "flash_mapping.h"
#include "hri_rtc_d51.h"
#include "hri_rstc_d51.h"
#include "driver_init.h"

#include "components/UpdateManager/UpdateManager.h"

static const void * s_fw_data = (const void *) FLASH_FW_OFFSET;

/**
 * The "RTC" define is located in a MCU header file such as "samd51p19a.h"
 */
static const void * s_rtc_module = (const void *) RTC;

static void JumpTargetFirmware (uint32_t jump_addr) {
    __asm__ (" mov   r1, %0        \n"
             " ldr   r0, [r1, #4]  \n"
             " ldr   sp, [r1]      \n"
             " blx   r0"
             : : "r" (jump_addr));
}

uint32_t FMP_ReadApplicationChecksum(void)
{
    return FLASH_HEADER->target_checksum;
}

/**
 * Read the RTC GP registers to check if the bootloader mode was requested
 *
 * The function returns false if the current RTC module setup
 * is not configured to support the RTC General Purpose Registers access,
 * or when the values in the GP registers do not correspond to booloader mode.
 *
 * The function returns true if GP registers are filled with 0xFFFFFFFF values,
 * which indicate that the
 */
StartupReason_t FMP_CheckBootloaderModeRequest(void) {

    uint32_t gp0, gp1, gp2, gp3 = 0u;
    StartupReason_t startupReason = StartupReason_PowerUp;

    // unresponsive application?
    bool wdt_reset = hri_rstc_get_RCAUSE_WDT_bit(RSTC);

    // Brown-out detection?
    bool bod12_reset = hri_rstc_get_RCAUSE_BODCORE_bit(RSTC);
    bool bod33_reset = hri_rstc_get_RCAUSE_BODVDD_bit(RSTC);

    if (wdt_reset)
    {
        startupReason = StartupReason_WatchdogReset;
    }
    else if (bod12_reset || bod33_reset)
    {
        startupReason = StartupReason_BrownOutReset;
    }
    // GP functionality should be ON (there are only GP0 and GP2 enable flags)
    else if (hri_rtcmode0_get_CTRLB_GP0EN_bit(s_rtc_module) && hri_rtcmode0_get_CTRLB_GP2EN_bit(s_rtc_module))
    {
        // Get the GP values
        gp0 = (uint32_t) hri_rtc_read_GP_reg(s_rtc_module, 0u);
        gp1 = (uint32_t) hri_rtc_read_GP_reg(s_rtc_module, 1u);
        gp2 = (uint32_t) hri_rtc_read_GP_reg(s_rtc_module, 2u);
        gp3 = (uint32_t) hri_rtc_read_GP_reg(s_rtc_module, 3u);

        // If all the three GP store values of 0xFFFFFFFF,
        // this means that we are requested to remain in the bootloader mode.
        // Now clear the registers and disable GP funcionality
        if ((gp0 & gp1 & gp2 & gp3) == 0xFFFFFFFFu) {
            hri_rtc_write_GP_reg(s_rtc_module, 0u, (hri_rtc_gp_reg_t) 0u);
            hri_rtc_write_GP_reg(s_rtc_module, 1u, (hri_rtc_gp_reg_t) 0u);
            hri_rtc_write_GP_reg(s_rtc_module, 2u, (hri_rtc_gp_reg_t) 0u);
            hri_rtc_write_GP_reg(s_rtc_module, 3u, (hri_rtc_gp_reg_t) 0u);
            hri_rtcmode0_clear_CTRLB_GP0EN_bit(s_rtc_module);
            hri_rtcmode0_clear_CTRLB_GP2EN_bit(s_rtc_module);
            startupReason = StartupReason_BootloaderRequest;
        }
    }

    return startupReason;
}

bool FMP_CheckTargetFirmware(bool check_expected_crc, uint32_t expected_crc) {

    uint32_t crc32 = 0xFFFFFFFFu;

    // Sanity check that the target firmware size fits the dedicated region
    if (FLASH_HEADER->target_length > FLASH_AVAILABLE) {
        return false;
    }
    // On request check that the stored CRC matches the expected
    if (check_expected_crc && (FLASH_HEADER->target_checksum != expected_crc)) {
        return false;
    }

    crc32 = CRC32_Calculate(crc32, s_fw_data, FLASH_HEADER->target_length);
    crc32 ^= 0xFFFFFFFFu; // Final CRC bit inversion as per algo specification

    return (crc32 == FLASH_HEADER->target_checksum);
}

static bool _is_region_empty(const uint32_t* ptr, size_t size) {
    for (size_t i = 0u; i < size / 4u; i++)
    {
        if (ptr[i] != 0xFFFFFFFFu)
        {
            return false;
        }
    }
    return true;
}

bool FMP_IsApplicationEmpty(void)
{
    return _is_region_empty((const uint32_t*) FLASH_ADDR, FLASH_AVAILABLE);
}

bool FMP_IsApplicationHeaderEmpty(void)
{
    return _is_region_empty((const uint32_t*) FLASH_HDR_OFFSET, NVMCTRL_BLOCK_SIZE);
}

void FMP_FixApplicationHeader(void)
{
    ApplicationFlashHeader_t header = {
        .bootloader_version = BOOTLOADER_VERSION,
        .hw_version = HARDWARE_VERSION,
        .target_checksum = 0xDEADBEEFu, /* doesn't matter in debug */
        .target_length = FLASH_AVAILABLE
    };
    UpdateManager_Run_UpdateApplicationHeader(&header);
}

void FMT_JumpTargetFirmware(void) {
    __disable_irq();
    watchdog_start();
    JumpTargetFirmware(FLASH_ADDR + FLASH_FW_OFFSET);
}

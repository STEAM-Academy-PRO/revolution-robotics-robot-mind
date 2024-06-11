#include "driver_init.h"

#include "CommonLibraries/functions.h"
#include "CommonLibraries/color.h"
#include "CommonLibraries/flash_mapping.h"
#include "rrrc/generated_runtime.h"

#include <math.h>

#include "CommonLibraries/log.h"

#ifdef DEBUG
#define DEBUG_SKIP_FW_INTEGRITY_CHECK 1
#else
#define DEBUG_SKIP_FW_INTEGRITY_CHECK 0
#endif

static bool jump_to_application = false;

static rgb_t ringLeds[12] = { 0 };
static bool ringLedsChanged;

extern uint32_t _srtt;
extern uint32_t _ertt;

static void clear_rtt(void) {
    // Clear the rtt segments
    for (uint32_t* pDest = &_srtt; pDest < &_ertt;) {
        *pDest++ = 0;
    }
}

int main(void)
{
    system_init();

    // FIXME: we need to initialize CRC here because the generated runtime starts later.
    CRC_Run_OnInit();

    // FIXME: we need to initialize CRC here because the generated runtime starts later.
    CRC_Run_OnInit();

    StartupReason_t startupReason = FMP_CheckBootloaderModeRequest();

    if (startupReason == StartupReason_PowerUp || startupReason == StartupReason_BrownOutReset)
    {
        clear_rtt();
    }

    LOG_INIT();

    switch (startupReason) {
        case StartupReason_PowerUp:
            LOG_RAW("Startup reason: Power up\n");
            break;
        case StartupReason_BootloaderRequest:
            LOG_RAW("Startup reason: Bootloader mode requested\n");
            break;
        case StartupReason_WatchdogReset:
            LOG_RAW("Startup reason: WDT reset\n");
            break;
        case StartupReason_BrownOutReset:
            LOG_RAW("Startup reason: brown-out event\n");
            break;
    }

    LOG_RAW("Starting bootloader\n");

    // We allow the app to start after a brown-out event. We trust the detector to prevent
    // incorrect behavior.
    if (startupReason == StartupReason_PowerUp || startupReason == StartupReason_BrownOutReset)
    {
        LOG_RAW("Checking firmware\n");
        /* TODO: debug bootloaders should look for empty header info and write it */

        bool start_application = FMP_FlashHeaderValid();

        if (!start_application) {
            LOG_RAW("Invalid firmware header\n");
        } else {
            uint32_t calculated_crc = FMP_CalculateFirmwareCRC();
            uint32_t recorded_crc = FMP_RecordedFirmwareCRC();

            start_application = (calculated_crc == recorded_crc);

            if (!start_application) {
                LOG("Firmware CRC mismatch: calculated %X, recorded %X\n", calculated_crc, recorded_crc);
            }
        }

#if DEBUG_SKIP_FW_INTEGRITY_CHECK
        if (!start_application)
        {
            LOG_RAW("Debug mode, application CRC mismatch\n");
            if (FMP_IsApplicationHeaderEmpty() || FLASH_HEADER->bootloader_version != BOOTLOADER_VERSION)
            {
                LOG_RAW("Debug mode, fixing up application header\n");
                ApplicationFlashHeader_t header = {
                    .bootloader_version = BOOTLOADER_VERSION,
                    .hw_version = HARDWARE_VERSION,
                    .target_checksum = 0xDEADBEEFu, /* doesn't matter in debug */
                    .target_length = FLASH_AVAILABLE
                };
                UpdateManager_Run_UpdateApplicationHeader(&header);
                NVIC_SystemReset();
            }
            start_application = !FMP_IsApplicationEmpty();
        }
#endif
        if (start_application)
        {
            LOG_RAW("Bootloader: Starting application\n");
            /* this should be the only application start point to avoid getting stuck in a hard fault */

            __disable_irq();
            watchdog_start();
            size_t jump_addr = FLASH_ADDR + FLASH_FW_OFFSET;
            __asm__ (" mov   r1, %0        \n"
                    " ldr   r0, [r1, #4]  \n"
                    " ldr   sp, [r1]      \n"
                    " blx   r0"
                    : : "r" (jump_addr));
        } else {
            LOG_RAW("No valid firmware found\n");
        }
    }

    LOG_RAW("Entered bootloader mode\n");
    // If we are below this line then there was either a bootloader request,
    // or the target firmware is missing or corrupted

    Runtime_RaiseEvent_OnInit();

    // Display some indication why we are in bootloader mode
    switch (startupReason) {
        case StartupReason_BootloaderRequest:
            // Bootloader mode was requested, do not show any indication
            break;

        case StartupReason_BrownOutReset:
        case StartupReason_PowerUp:
            // We did not find any loadable application. Display an angry red light on the
            // bottom-most ring LED to indicate this.
            ringLeds[5] = (rgb_t) LED_RED;
            break;

        case StartupReason_WatchdogReset:
            // The application is most likely inoperable. Display an angry red light on the
            // top and bottom ring LED to indicate this.
            ringLeds[5] = (rgb_t) LED_RED;
            ringLeds[11] = (rgb_t) LED_RED;
            break;
    }

    Runtime_RaiseEvent_OnInitDone();

    while (1) {
        Runtime_RaiseEvent_Loop();
    }
}

void MasterCommunicationInterface_Bootloader_Read_Configuration(MasterCommunicationInterface_Config_t* dst)
{
    dst->default_response = MasterCommunication_Constant_DefaultResponse();
    dst->rx_overflow_response = MasterCommunication_Constant_LongRxErrorResponse();
}

void CommHandlers_RequestJumpToApplication(void)
{
    jump_to_application = true;
}

void MasterCommunicationInterface_Bootloader_RaiseEvent_OnTransmissionComplete(void)
{
    if (jump_to_application)
    {
        /* Reset here - firmware will be loaded at the beginning of the bootloader execution */
        NVIC_SystemReset();
    }
}

rgb_t LEDController_Read_RingLED(uint32_t led_idx)
{
    if (led_idx >= ARRAY_SIZE(ringLeds))
    {
        return (rgb_t) LED_OFF;
    }
    else
    {
        return ringLeds[led_idx];
    }
}

bool LEDController_Read_RingLEDs_Changed(void)
{
    bool changed = ringLedsChanged;
    ringLedsChanged = false;
    return changed;
}

void UpdateManager_RaiseEvent_ProgressChanged(uint8_t progress)
{
    uint8_t n_leds = (uint8_t) lroundf(map(progress, 0, 255, 0, 12));
    for (uint8_t i = 0u; i < n_leds; i++)
    {
        ringLeds[i] = (rgb_t) LED_CYAN;
    }
    for (uint8_t i = n_leds; i < 12; i++)
    {
        ringLeds[i] = (rgb_t) LED_OFF;
    }
}

void assert_failed(const char *file, uint32_t line)
{
    LOG("Bootloader Assert failed at line %u of %s\n", line, file);
    __BKPT(0);
}

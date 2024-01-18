#include <atmel_start.h>
#include "crc32_software.h"
#include "flash_mapping.h"

#include "rrrc/utils/functions.h"
#include "rrrc/runtime/runtime.h"
#include "rrrc/include/color.h"

#include <math.h>

#ifdef DEBUG
#define DEBUG_SKIP_FW_INTEGRITY_CHECK 1
#else
#define DEBUG_SKIP_FW_INTEGRITY_CHECK 0
#endif

static MasterCommunicationInterface_Config_t communicationConfig = 
{
};

static bool jump_to_application = false;

static rgb_t ringLeds[12] = { 0 };
static bool ringLedsChanged;

int main(void)
{
    /* Perform the very basic init and check the bootloader mode request */
    init_mcu();
    CRC32_Init();
    StartupReason_t startupReason = FMP_CheckBootloaderModeRequest();
    if (startupReason == StartupReason_PowerUp)
    {
        /* TODO: debug bootloaders should look for empty header info and write it */
        bool start_application = FMP_CheckTargetFirmware(false, 0u);
#if DEBUG_SKIP_FW_INTEGRITY_CHECK
        if (!start_application)
        {
            if (FMP_IsApplicationHeaderEmpty() || FLASH_HEADER->bootloader_version != BOOTLOADER_VERSION)
            {
                atmel_start_init();
                FMP_FixApplicationHeader();
                NVIC_SystemReset();
            }
            start_application = !FMP_IsApplicationEmpty();
        }
#endif
        if (start_application)
        {
            /* this should be the only application start point to avoid getting stuck in a hard fault */
            FMT_JumpTargetFirmware();
        }
    }

    // If we are below this line then there was either a bootloader request,
    // or the target firmware is missing or corrupted

    // Initializes MCU, drivers and middleware
    atmel_start_init();

    MasterCommunication_Run_OnInit(&communicationHandlers[0], COMM_HANDLER_COUNT);

    MasterCommunication_Run_GetDefaultResponse(&communicationConfig.defaultResponseBuffer, &communicationConfig.defaultResponseLength);
    MasterCommunication_Run_GetLongRxErrorResponse(&communicationConfig.longRxErrorResponseBuffer, &communicationConfig.longRxErrorResponseLength);

    MasterCommunicationInterface_Run_OnInit(&communicationConfig);

    LEDController_Run_OnInit();

    while (1) {
        MasterCommunicationInterface_Run_Update();
        LEDController_Run_Update();
    }
}

void MasterCommunicationInterface_Call_OnMessageReceived(const uint8_t* buffer, size_t bufferSize)
{
    MasterCommunication_Run_HandleCommand(buffer, bufferSize);
}

void MasterCommunication_Call_SendResponse(const uint8_t* responseBuffer, size_t responseSize)
{
    MasterCommunicationInterface_Run_SetResponse(responseBuffer, responseSize);
}

void Runtime_RequestJumpToApplication(void)
{
    jump_to_application = true;
}

void MasterCommunicationInterface_Call_OnTransmitComplete(void)
{
    if (jump_to_application)
    {
        FMT_JumpTargetFirmware();
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

void UpdateManager_Write_Progress(uint8_t progress)
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
    __BKPT(0);
}

#include <atmel_start.h>
#include "flash_mapping.h"

#include "utils/crc.h"
#include "rrrc/utils/functions.h"
#include "rrrc/runtime/runtime.h"
#include "rrrc/include/color.h"

#include <math.h>

#include "SEGGER_RTT.h"

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

extern uint32_t _srtt;
extern uint32_t _ertt;

static void clear_rtt() {
    // Clear the rtt segments
    for (uint32_t* pDest = &_srtt; pDest < &_ertt;) {
        *pDest++ = 0;
    }

}

int main(void)
{
    /* Perform the very basic init and check the bootloader mode request */
    init_mcu();
    CRC32_Init();

    StartupReason_t startupReason = FMP_CheckBootloaderModeRequest();

    if (startupReason == StartupReason_PowerUp)
    {
        clear_rtt();
    }

    SEGGER_RTT_ConfigUpBuffer(0, NULL, NULL, 0, SEGGER_RTT_MODE_NO_BLOCK_SKIP);

    switch (startupReason) {
        case StartupReason_PowerUp:
            SEGGER_RTT_WriteString(0, "Startup reason: Power up\r\n");
            break;
        case StartupReason_BootloaderRequest:
            SEGGER_RTT_WriteString(0, "Startup reason: Bootloader mode requested\r\n");
            break;
        case StartupReason_WatchdogReset:
            SEGGER_RTT_WriteString(0, "Startup reason: WDT reset\r\n");
            break;
    }

    SEGGER_RTT_WriteString(0, "Starting bootloader\r\n");

    if (startupReason == StartupReason_PowerUp)
    {
        SEGGER_RTT_WriteString(0, "Checking firmware\r\n");
        /* TODO: debug bootloaders should look for empty header info and write it */
        bool start_application = FMP_CheckTargetFirmware(false, 0u);
#if DEBUG_SKIP_FW_INTEGRITY_CHECK
        if (!start_application)
        {
            if (FMP_IsApplicationHeaderEmpty() || FLASH_HEADER->bootloader_version != BOOTLOADER_VERSION)
            {
                SEGGER_RTT_WriteString(0, "Debug mode, fixing up application header\r\n");
                atmel_start_init();
                FMP_FixApplicationHeader();
                NVIC_SystemReset();
            }
            start_application = !FMP_IsApplicationEmpty();
        }
#endif
        if (start_application)
        {
            SEGGER_RTT_WriteString(0, "Starting application\r\n");
            /* this should be the only application start point to avoid getting stuck in a hard fault */
            FMT_JumpTargetFirmware();
        }
    }

    SEGGER_RTT_WriteString(0, "Entered bootloader mode\r\n");
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

#include <atmel_start.h>
#include "flash_mapping.h"

#include "rrrc/libraries/functions.h"
#include "rrrc/runtime/runtime.h"
#include "rrrc/libraries/crc.h"
#include "rrrc/generated_runtime.h"
#include "libraries/color.h"

#include <math.h>

#include "SEGGER_RTT.h"

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
    atmel_start_init();

    StartupReason_t startupReason = FMP_CheckBootloaderModeRequest();

    if (startupReason == StartupReason_PowerUp || startupReason == StartupReason_BrownOutReset)
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
        case StartupReason_BrownOutReset:
            SEGGER_RTT_WriteString(0, "Startup reason: brown-out event\r\n");
            break;
    }

    SEGGER_RTT_WriteString(0, "Starting bootloader\r\n");

    // We allow the app to start after a brown-out event. We trust the detector to prevent
    // incorrect behavior.
    if (startupReason == StartupReason_PowerUp || startupReason == StartupReason_BrownOutReset)
    {
        SEGGER_RTT_WriteString(0, "Checking firmware\r\n");
        /* TODO: debug bootloaders should look for empty header info and write it */
        bool start_application = FMP_CheckTargetFirmware(false, 0u);
#if DEBUG_SKIP_FW_INTEGRITY_CHECK
        if (!start_application)
        {
            SEGGER_RTT_WriteString(0, "Debug mode, application CRC mismatch\r\n");
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
            SEGGER_RTT_WriteString(0, "Bootloader: Starting application\r\n");
            /* this should be the only application start point to avoid getting stuck in a hard fault */
            FMT_JumpTargetFirmware();
        } else {
            SEGGER_RTT_WriteString(0, "No valid firmware found\r\n");
        }
    }

    SEGGER_RTT_WriteString(0, "Entered bootloader mode\r\n");
    // If we are below this line then there was either a bootloader request,
    // or the target firmware is missing or corrupted

    Runtime_RaiseEvent_OnInit();
    MasterCommunication_Run_OnInit();

    // Display some indication why we are in bootloader mode
    switch (startupReason) {
        case StartupReason_BootloaderRequest:
            // Bootloader mode was requested, do not show any indication
            break;

        case StartupReason_BrownOutReset:
        case StartupReason_PowerUp:
            // We did not find any loadable application. Display an angry red light on the
            // bottom-most ring LED to indicate this.
            ringLeds[2] = (rgb_t) LED_RED;
            break;

        case StartupReason_WatchdogReset:
            // The application is most likely inoperable. Display an angry red light on the
            // top and bottom ring LED to indicate this.
            ringLeds[2] = (rgb_t) LED_RED;
            ringLeds[8] = (rgb_t) LED_RED;
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

void MasterCommunicationInterface_Bootloader_RaiseEvent_OnMessageReceived(ConstByteArray_t message)
{
    MasterCommunication_Run_HandleCommand(message);
}

void MasterCommunication_Call_SendResponse(ConstByteArray_t response)
{
    MasterCommunicationInterface_Bootloader_Run_SetResponse(response);
}

void Runtime_RequestJumpToApplication(void)
{
    jump_to_application = true;
}

void MasterCommunicationInterface_Bootloader_RaiseEvent_OnTransmissionComplete(void)
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

uint8_t MasterCommunication_Call_Calculate_CRC7(uint8_t init_value, ConstByteArray_t data)
{
    return CRC7_Calculate(init_value, data.bytes, data.count);
}

uint16_t MasterCommunication_Call_Calculate_CRC16(uint16_t init_value, ConstByteArray_t data)
{
    return CRC16_Calculate(init_value, data.bytes, data.count);
}

void assert_failed(const char *file, uint32_t line)
{
    SEGGER_RTT_printf(0, "Bootloader Assert failed at line %u of %s\r\n", line, file);
    __BKPT(0);
}

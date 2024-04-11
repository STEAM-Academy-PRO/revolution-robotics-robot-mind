#include "runtime.h"

#include "flash_mapping.h"
#include "CommonLibraries/converter.h"
#include "utils.h"

#include <string.h>
#include "SEGGER_RTT.h"

/* These constants are common between bootloader and application */
#define OPERATION_MODE_BOOTLOADER   ((uint8_t) 0xBBu)
#define OPERATION_MODE_APPLICATION  ((uint8_t) 0xAAu)

static Comm_Status_t GetOperationMode_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount);
static Comm_Status_t InitializeUpdate_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount);
static Comm_Status_t ProgramApplication_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount);
static Comm_Status_t FinalizeUpdate_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount);
static Comm_Status_t ReadApplicationCrc_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount);
static Comm_Status_t VersionProvider_GetHardwareVersion_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount);

/* These commands relate to BootloaderControl in pi-firmware/revvy/mcu/rrrc_control.py */
Comm_CommandHandler_t communicationHandlers[COMM_HANDLER_COUNT] =
{
    [0x01u] = { .Start = &VersionProvider_GetHardwareVersion_Start, .GetResult = NULL, .ExecutionInProgress = false  },

    /* [0x06 - 0x0A]: reserved for bootloader */
    [0x06u] = { .Start = &GetOperationMode_Start, .GetResult = NULL, .ExecutionInProgress = false  },
    [0x07u] = { .Start = &ReadApplicationCrc_Start, .GetResult = NULL, .ExecutionInProgress = false  },
    [0x08u] = { .Start = &InitializeUpdate_Start, .GetResult = NULL, .ExecutionInProgress = false  },
    [0x09u] = { .Start = &ProgramApplication_Start, .GetResult = NULL, .ExecutionInProgress = false  },
    [0x0Au] = { .Start = &FinalizeUpdate_Start, .GetResult = NULL, .ExecutionInProgress = false  },
};

static Comm_Status_t GetOperationMode_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount)
{
    (void) commandPayload;

    SEGGER_RTT_printf(0, "GetOperationMode\n");
    response.bytes[0] = OPERATION_MODE_BOOTLOADER;
    *responseCount = 1u;
    return Comm_Status_Ok;
}

static Comm_Status_t ReadApplicationCrc_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount)
{
    (void) commandPayload;

    SEGGER_RTT_printf(0, "ReadApplicationCrc\n");
    uint32_t checksum = FMP_ReadApplicationChecksum();
    memcpy(&response.bytes[0], &checksum, 4u);
    *responseCount = 4u;
    return Comm_Status_Ok;
}

static Comm_Status_t InitializeUpdate_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount)
{
    (void) response;
    (void) responseCount;

    SEGGER_RTT_printf(0, "InitializeUpdate\n");
    if (commandPayload.count != 8u)
    {
        return Comm_Status_Error_PayloadLengthError;
    }

    /* check whether the image fits in flash memory */
    size_t firmware_size = get_uint32(&commandPayload.bytes[0]);
    uint32_t checksum = get_uint32(&commandPayload.bytes[4]);

    // TODO: this should be an async server call. The operation takes long and the RPi may time out.

    if (!UpdateManager_Run_CheckImageFitsInFlash(firmware_size))
    {
        return Comm_Status_Error_CommandError;
    }

    UpdateManager_Run_InitializeUpdate(firmware_size, checksum);

    return Comm_Status_Ok;
}

static Comm_Status_t ProgramApplication_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount)
{
    (void) response;
    (void) responseCount;

    SEGGER_RTT_printf(0, "ProgramApplication\n");
    switch (UpdateManager_Run_WriteNextChunk(commandPayload))
    {
        case UpdateManager_Ok:
            return Comm_Status_Ok;

        default:
            return Comm_Status_Error_CommandError;
    }
}

static Comm_Status_t FinalizeUpdate_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount)
{
    (void) commandPayload;
    (void) response;
    (void) responseCount;

    SEGGER_RTT_printf(0, "FinalizeUpdate\n");
    switch (UpdateManager_Run_Finalize())
    {
        case UpdateManager_Ok:
            Runtime_RequestJumpToApplication();
            return Comm_Status_Ok;

        default:
            return Comm_Status_Error_CommandError;
    }
}

static Comm_Status_t VersionProvider_GetHardwareVersion_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount)
{
    (void) commandPayload;

    static const char* hw_version_strings[] =
    {
        "1.0.0",
        "1.0.1",
        "2.0.0"
    };

    SEGGER_RTT_printf(0, "GetHardwareVersion\n");
    uint32_t hw = HARDWARE_VERSION;

    if (hw < ARRAY_SIZE(hw_version_strings))
    {
        uint8_t len = strlen(hw_version_strings[hw]);
        memcpy(response.bytes, hw_version_strings[hw], len);
        *responseCount = len;

        return Comm_Status_Ok;
    }
    else
    {
        return Comm_Status_Error_InternalError;
    }
}

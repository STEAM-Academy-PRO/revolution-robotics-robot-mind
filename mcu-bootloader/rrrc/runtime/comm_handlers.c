#include "runtime.h"

#include "flash_mapping.h"
#include "../utils/converter.h"

#include <string.h> // memcpy
#include "SEGGER_RTT.h"

/* These constants are common between bootloader and application */
#define OPERATION_MODE_BOOTLOADER   ((uint8_t) 0xBBu)
#define OPERATION_MODE_APPLICATION  ((uint8_t) 0xAAu)

static Comm_Status_t GetOperationMode_Start(const uint8_t* commandPayload, uint8_t commandSize, uint8_t* response, uint8_t responseBufferSize, uint8_t* responseCount);
static Comm_Status_t InitializeUpdate_Start(const uint8_t* commandPayload, uint8_t commandSize, uint8_t* response, uint8_t responseBufferSize, uint8_t* responseCount);
static Comm_Status_t ProgramApplication_Start(const uint8_t* commandPayload, uint8_t commandSize, uint8_t* response, uint8_t responseBufferSize, uint8_t* responseCount);
static Comm_Status_t FinalizeUpdate_Start(const uint8_t* commandPayload, uint8_t commandSize, uint8_t* response, uint8_t responseBufferSize, uint8_t* responseCount);
static Comm_Status_t ReadApplicationCrc_Start(const uint8_t* commandPayload, uint8_t commandSize, uint8_t* response, uint8_t responseBufferSize, uint8_t* responseCount);

const Comm_CommandHandler_t communicationHandlers[COMM_HANDLER_COUNT] = 
{
    [0x01u] = { .Start = &VersionProvider_GetHardwareVersion_Start, .GetResult = NULL, .Cancel = NULL },

    /* [0x06 - 0x0A]: reserved for bootloader */
    [0x06] = { .Start = &GetOperationMode_Start, .GetResult = NULL, .Cancel = NULL },
    [0x07] = { .Start = &ReadApplicationCrc_Start, .GetResult = NULL, .Cancel = NULL },
    [0x08] = { .Start = &InitializeUpdate_Start, .GetResult = NULL, .Cancel = NULL },
    [0x09] = { .Start = &ProgramApplication_Start, .GetResult = NULL, .Cancel = NULL },
    [0x0A] = { .Start = &FinalizeUpdate_Start, .GetResult = NULL, .Cancel = NULL },
};

static Comm_Status_t GetOperationMode_Start(const uint8_t* commandPayload, uint8_t commandSize, uint8_t* response, uint8_t responseBufferSize, uint8_t* responseCount)
{
    (void) commandPayload;
    (void) commandSize;
    (void) responseBufferSize;

    SEGGER_RTT_printf(0, "GetOperationMode\n");
    *response = OPERATION_MODE_BOOTLOADER;
    *responseCount = 1u;
    return Comm_Status_Ok;
}

static Comm_Status_t ReadApplicationCrc_Start(const uint8_t* commandPayload, uint8_t commandSize, uint8_t* response, uint8_t responseBufferSize, uint8_t* responseCount)
{
    (void) commandPayload;
    (void) commandSize;
    (void) responseBufferSize;

    SEGGER_RTT_printf(0, "ReadApplicationCrc\n");
    uint32_t checksum = FMP_ReadApplicationChecksum();
    memcpy(response, &checksum, 4u);
    *responseCount = 4u;
    return Comm_Status_Ok;
}

static Comm_Status_t InitializeUpdate_Start(const uint8_t* commandPayload, uint8_t commandSize, uint8_t* response, uint8_t responseBufferSize, uint8_t* responseCount)
{
    (void) response;
    (void) responseBufferSize;
    (void) responseCount;

    SEGGER_RTT_printf(0, "InitializeUpdate\n");
    if (commandSize != 8u)
    {
        return Comm_Status_Error_PayloadLengthError;
    }

    /* check whether the image fits in flash memory */
    size_t firmware_size = get_uint32(&commandPayload[0]);
    uint32_t checksum = get_uint32(&commandPayload[4]);
    
    if (!UpdateManager_Run_CheckImageFitsInFlash(firmware_size))
    {
        return Comm_Status_Error_CommandError;
    }

    UpdateManager_Run_InitializeUpdate(firmware_size, checksum);

    return Comm_Status_Ok;
}

static Comm_Status_t ProgramApplication_Start(const uint8_t* commandPayload, uint8_t commandSize, uint8_t* response, uint8_t responseBufferSize, uint8_t* responseCount)
{
    (void) responseBufferSize;
    (void) response;
    (void) responseCount;

    SEGGER_RTT_printf(0, "ProgramApplication\n");
    switch (UpdateManager_Run_Program(commandPayload, commandSize))
    {
        case UpdateManager_Ok:
            return Comm_Status_Ok;

        default:
            return Comm_Status_Error_CommandError;
    }
}

static Comm_Status_t FinalizeUpdate_Start(const uint8_t* commandPayload, uint8_t commandSize, uint8_t* response, uint8_t responseBufferSize, uint8_t* responseCount)
{
    (void) commandPayload;
    (void) commandSize;
    (void) response;
    (void) responseBufferSize;
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

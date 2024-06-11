#include "CommWrapper_Bootloader.h"
#include "utils.h"

/* Begin User Code Section: Declarations */
#include "utils_assert.h"
#include "CommonLibraries/log.h"
#include "CommonLibraries/flash_mapping.h"
#include <string.h>

/* These constants are common between bootloader and application */
#define OPERATION_MODE_BOOTLOADER   ((uint8_t) 0xBBu)
#define OPERATION_MODE_APPLICATION  ((uint8_t) 0xAAu)

/* End User Code Section: Declarations */

Comm_Status_t CommWrapper_Bootloader_Run_Command_GetOperationMode_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount)
{
    /* Begin User Code Section: Command_GetOperationMode_Start:run Start */
    if (commandPayload.count != 0u)
    {
        return Comm_Status_Error_PayloadLengthError;
    }

    ASSERT(response.count >= 1u);
    response.bytes[0] = OPERATION_MODE_APPLICATION;
    *responseCount = 1u;

    return Comm_Status_Ok;
    /* End User Code Section: Command_GetOperationMode_Start:run Start */
    /* Begin User Code Section: Command_GetOperationMode_Start:run End */

    /* End User Code Section: Command_GetOperationMode_Start:run End */
}

Comm_Status_t CommWrapper_Bootloader_Run_Command_ReadApplicationCrc_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount)
{
    /* Begin User Code Section: Command_ReadApplicationCrc_Start:run Start */
    (void) commandPayload;

    LOG_RAW("ReadApplicationCrc\n");
    uint32_t checksum = FMP_ReadApplicationChecksum();
    memcpy(&response.bytes[0], &checksum, 4u);
    *responseCount = 4u;
    return Comm_Status_Ok;
    /* End User Code Section: Command_ReadApplicationCrc_Start:run Start */
    /* Begin User Code Section: Command_ReadApplicationCrc_Start:run End */

    /* End User Code Section: Command_ReadApplicationCrc_Start:run End */
}

Comm_Status_t CommWrapper_Bootloader_Run_Command_RebootToBootloader_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount)
{
    /* Begin User Code Section: Command_RebootToBootloader_Start:run Start */
    (void) response;
    (void) responseCount;

    if (commandPayload.count != 0u)
    {
        return Comm_Status_Error_PayloadLengthError;
    }

    CommWrapper_Bootloader_Async_RebootToBootloader_Call();

    return Comm_Status_Ok;
    /* End User Code Section: Command_RebootToBootloader_Start:run Start */
    /* Begin User Code Section: Command_RebootToBootloader_Start:run End */

    /* End User Code Section: Command_RebootToBootloader_Start:run End */
}

__attribute__((weak))
AsyncOperationState_t CommWrapper_Bootloader_Async_RebootToBootloader_Call(void)
{
    /* Begin User Code Section: RebootToBootloader:async_call Start */

    /* End User Code Section: RebootToBootloader:async_call Start */
    /* Begin User Code Section: RebootToBootloader:async_call End */

    /* End User Code Section: RebootToBootloader:async_call End */
    return AsyncOperationState_Busy;
}

__attribute__((weak))
AsyncOperationState_t CommWrapper_Bootloader_Async_RebootToBootloader_GetResult(void)
{
    /* Begin User Code Section: RebootToBootloader:get_result Start */

    /* End User Code Section: RebootToBootloader:get_result Start */
    /* Begin User Code Section: RebootToBootloader:get_result End */

    /* End User Code Section: RebootToBootloader:get_result End */
    return AsyncOperationState_Busy;
}

__attribute__((weak))
void CommWrapper_Bootloader_Async_RebootToBootloader_Cancel(void)
{
    /* Begin User Code Section: RebootToBootloader:cancel Start */

    /* End User Code Section: RebootToBootloader:cancel Start */
    /* Begin User Code Section: RebootToBootloader:cancel End */

    /* End User Code Section: RebootToBootloader:cancel End */
}

#include "CommWrapper_ErrorStorage.h"
#include "utils.h"

/* Begin User Code Section: Declarations */
#include "error_ids.h"
#include "CommonLibraries/converter.h"
#include <string.h>
#include "utils_assert.h"
/* End User Code Section: Declarations */

Comm_Status_t CommWrapper_ErrorStorage_Run_Command_ReadCount_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount)
{
    /* Begin User Code Section: Command_ReadCount_Start:run Start */
    if (commandPayload.count != 0u)
    {
        return Comm_Status_Error_PayloadLengthError;
    }

    ASSERT(response.count >= sizeof(uint32_t));

    uint32_t count = CommWrapper_ErrorStorage_Read_NumberOfStoredErrors();

    memcpy(response.bytes, &count, sizeof(uint32_t));
    *responseCount = sizeof(uint32_t);

    return Comm_Status_Ok;
    /* End User Code Section: Command_ReadCount_Start:run Start */
    /* Begin User Code Section: Command_ReadCount_Start:run End */

    /* End User Code Section: Command_ReadCount_Start:run End */
}

Comm_Status_t CommWrapper_ErrorStorage_Run_Command_ReadErrors_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount)
{
    /* Begin User Code Section: Command_ReadErrors_Start:run Start */
    if (commandPayload.count != 4u)
    {
        return Comm_Status_Error_PayloadLengthError;
    }

    ASSERT(response.count >= sizeof(ErrorInfo_t));

    uint32_t count = CommWrapper_ErrorStorage_Read_NumberOfStoredErrors();
    uint32_t start = get_uint32(commandPayload.bytes);

    for (uint32_t i = start; i < count; i++)
    {
        if (*responseCount + sizeof(ErrorInfo_t) <= response.count)
        {
            ErrorInfo_t error;
            if (CommWrapper_ErrorStorage_Call_Read(i, &error))
            {
                memcpy(&response.bytes[*responseCount], &error, sizeof(ErrorInfo_t));
                *responseCount += sizeof(ErrorInfo_t);
            }
        }
        else
        {
            break;
        }
    }

    return Comm_Status_Ok;
    /* End User Code Section: Command_ReadErrors_Start:run Start */
    /* Begin User Code Section: Command_ReadErrors_Start:run End */

    /* End User Code Section: Command_ReadErrors_Start:run End */
}

Comm_Status_t CommWrapper_ErrorStorage_Run_Command_ClearMemory_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount)
{
    /* Begin User Code Section: Command_ClearMemory_Start:run Start */
    (void) response;
    (void) responseCount;

    if (commandPayload.count != 0u)
    {
        return Comm_Status_Error_PayloadLengthError;
    }
    CommWrapper_ErrorStorage_Call_ClearMemory();

    return Comm_Status_Ok;
    /* End User Code Section: Command_ClearMemory_Start:run Start */
    /* Begin User Code Section: Command_ClearMemory_Start:run End */

    /* End User Code Section: Command_ClearMemory_Start:run End */
}

Comm_Status_t CommWrapper_ErrorStorage_Run_Command_StoreTestError_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount)
{
    /* Begin User Code Section: Command_StoreTestError_Start:run Start */
    (void) response;
    (void) responseCount;

    if (commandPayload.count != 0u)
    {
        return Comm_Status_Error_PayloadLengthError;
    }

    ErrorInfo_t error;
    error.error_id = ERROR_ID_TEST_ERROR;
    for (uint32_t i = 0u; i < sizeof(error.data); i++)
    {
        error.data[i] = (uint8_t) (i % 256u);
    }

    CommWrapper_ErrorStorage_Call_Store(&error);
    return Comm_Status_Ok;
    /* End User Code Section: Command_StoreTestError_Start:run Start */
    /* Begin User Code Section: Command_StoreTestError_Start:run End */

    /* End User Code Section: Command_StoreTestError_Start:run End */
}

__attribute__((weak))
bool CommWrapper_ErrorStorage_Call_Read(uint32_t index, ErrorInfo_t* error)
{
    (void) error;
    (void) index;
    /* Begin User Code Section: Read:run Start */

    /* End User Code Section: Read:run Start */
    /* Begin User Code Section: Read:run End */

    /* End User Code Section: Read:run End */
    return false;
}

__attribute__((weak))
void CommWrapper_ErrorStorage_Call_Store(const ErrorInfo_t* error)
{
    (void) error;
    /* Begin User Code Section: Store:run Start */

    /* End User Code Section: Store:run Start */
    /* Begin User Code Section: Store:run End */

    /* End User Code Section: Store:run End */
}

__attribute__((weak))
void CommWrapper_ErrorStorage_Call_ClearMemory(void)
{
    /* Begin User Code Section: ClearMemory:run Start */

    /* End User Code Section: ClearMemory:run Start */
    /* Begin User Code Section: ClearMemory:run End */

    /* End User Code Section: ClearMemory:run End */
}

__attribute__((weak))
uint32_t CommWrapper_ErrorStorage_Read_NumberOfStoredErrors(void)
{
    /* Begin User Code Section: NumberOfStoredErrors:read Start */

    /* End User Code Section: NumberOfStoredErrors:read Start */
    /* Begin User Code Section: NumberOfStoredErrors:read End */

    /* End User Code Section: NumberOfStoredErrors:read End */
    return 0u;
}

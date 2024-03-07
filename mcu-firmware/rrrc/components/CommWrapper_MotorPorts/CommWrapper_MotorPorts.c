#include "CommWrapper_MotorPorts.h"
#include "utils.h"
#include "utils_assert.h"

/* Begin User Code Section: Declarations */
#include "SEGGER_RTT.h"
#include <string.h>

static uint8_t config_buffer[256];

#define MOTOR_PORT_IDX(x) ((x) - 1u)
/* End User Code Section: Declarations */

Comm_Status_t CommWrapper_MotorPorts_Run_Command_GetPortAmount_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount)
{
    /* Begin User Code Section: Command_GetPortAmount_Start:run Start */
    if (commandPayload.count != 0u)
    {
        return Comm_Status_Error_PayloadLengthError;
    }

    ASSERT(response.count >= 1u);
    response.bytes[0] = CommWrapper_MotorPorts_Read_PortCount();
    *responseCount = 1u;

    return Comm_Status_Ok;
    /* End User Code Section: Command_GetPortAmount_Start:run Start */
    /* Begin User Code Section: Command_GetPortAmount_Start:run End */

    /* End User Code Section: Command_GetPortAmount_Start:run End */
}

Comm_Status_t CommWrapper_MotorPorts_Run_Command_GetPortTypes_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount)
{
    /* Begin User Code Section: Command_GetPortTypes_Start:run Start */
    if (commandPayload.count != 0u)
    {
        return Comm_Status_Error_PayloadLengthError;
    }

    CommWrapper_MotorPorts_Call_ReadPortTypes(&response);
    if (responseCount != NULL)
    {
        *responseCount = response.count;
    }

    if (response.count == 0u)
    {
        return Comm_Status_Error_InternalError;
    }
    else
    {
        return Comm_Status_Ok;
    }
    /* End User Code Section: Command_GetPortTypes_Start:run Start */
    /* Begin User Code Section: Command_GetPortTypes_Start:run End */

    /* End User Code Section: Command_GetPortTypes_Start:run End */
}

Comm_Status_t CommWrapper_MotorPorts_Run_Command_SetPortType_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount)
{
    /* Begin User Code Section: Command_SetPortType_Start:run Start */
    (void) response;
    (void) responseCount;

    if (commandPayload.count != 2u)
    {
        return Comm_Status_Error_PayloadLengthError;
    }

    uint8_t port_idx = MOTOR_PORT_IDX(commandPayload.bytes[0]);
    uint8_t port_type = commandPayload.bytes[1];

    if (CommWrapper_MotorPorts_Async_SetPortType_Call(port_idx, port_type) == AsyncOperationState_Started)
    {
        return Comm_Status_Pending;
    }
    else
    {
        return Comm_Status_Error_InternalError;
    }
    /* End User Code Section: Command_SetPortType_Start:run Start */
    /* Begin User Code Section: Command_SetPortType_Start:run End */

    /* End User Code Section: Command_SetPortType_Start:run End */
}

Comm_Status_t CommWrapper_MotorPorts_Run_Command_SetPortType_GetResult(ByteArray_t response, uint8_t* responseCount)
{
    /* Begin User Code Section: Command_SetPortType_GetResult:run Start */
    (void) response;
    (void) responseCount;

    bool result;
    switch (CommWrapper_MotorPorts_Async_SetPortType_GetResult(&result))
    {
        case AsyncOperationState_Done:
            if (result)
            {
                return Comm_Status_Ok;
            }
            else
            {
                return Comm_Status_Error_CommandError;
            }
            break;

        case AsyncOperationState_Busy:
            return Comm_Status_Pending;

        default:
            return Comm_Status_Error_InternalError;
    }
    /* End User Code Section: Command_SetPortType_GetResult:run Start */
    /* Begin User Code Section: Command_SetPortType_GetResult:run End */

    /* End User Code Section: Command_SetPortType_GetResult:run End */
}

Comm_Status_t CommWrapper_MotorPorts_Run_Command_SetPortConfig_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount)
{
    /* Begin User Code Section: Command_SetPortConfig_Start:run Start */
    (void) response;
    (void) responseCount;

    if (commandPayload.count == 0u || commandPayload.count > ARRAY_SIZE(config_buffer) + 1u)
    {
        SEGGER_RTT_printf(0, "Payload length error (%u)\n", commandPayload.count);
        return Comm_Status_Error_PayloadLengthError;
    }

    uint8_t port_idx = MOTOR_PORT_IDX(commandPayload.bytes[0]);
    memcpy(config_buffer, &commandPayload.bytes[1], commandPayload.count - 1u);

    ByteArray_t config = {
        .bytes = config_buffer,
        .count = commandPayload.count - 1u
    };
    if (CommWrapper_MotorPorts_Async_SetPortConfig_Call(port_idx, config) == AsyncOperationState_Started)
    {
        return Comm_Status_Pending;
    }
    else
    {
        return Comm_Status_Error_InternalError;
    }
    /* End User Code Section: Command_SetPortConfig_Start:run Start */
    /* Begin User Code Section: Command_SetPortConfig_Start:run End */

    /* End User Code Section: Command_SetPortConfig_Start:run End */
}

Comm_Status_t CommWrapper_MotorPorts_Run_Command_SetPortConfig_GetResult(ByteArray_t response, uint8_t* responseCount)
{
    /* Begin User Code Section: Command_SetPortConfig_GetResult:run Start */
    (void) response;
    (void) responseCount;

    bool result;
    switch (CommWrapper_MotorPorts_Async_SetPortConfig_GetResult(&result))
    {
        case AsyncOperationState_Done:
            if (result)
            {
                return Comm_Status_Ok;
            }
            else
            {
                return Comm_Status_Error_CommandError;
            }
            break;

        case AsyncOperationState_Busy:
            return Comm_Status_Pending;

        default:
            return Comm_Status_Error_InternalError;
    }
    /* End User Code Section: Command_SetPortConfig_GetResult:run Start */
    /* Begin User Code Section: Command_SetPortConfig_GetResult:run End */

    /* End User Code Section: Command_SetPortConfig_GetResult:run End */
}

Comm_Status_t CommWrapper_MotorPorts_Run_Command_SetControlValue_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount)
{
    /* Begin User Code Section: Command_SetControlValue_Start:run Start */
    uint8_t processedBytes = 0u;
    size_t command_index = 0;
    while (processedBytes < commandPayload.count)
    {
        uint8_t segmentHeader = commandPayload.bytes[processedBytes];
        uint8_t segmentDataLength = (segmentHeader & 0xF8u) >> 3;
        uint8_t portIdx = (segmentHeader & 0x07u); // port idx is indexed from 0 here

        if (portIdx >= CommWrapper_MotorPorts_Read_PortCount())
        {
            *responseCount = 0u;
            return Comm_Status_Error_CommandError;
        }

        if (portIdx > response.count)
        {
            *responseCount = 0u;
            return Comm_Status_Error_CommandError;
        }

        ++processedBytes;

        if (segmentDataLength + processedBytes > commandPayload.count)
        {
            return Comm_Status_Error_PayloadLengthError;
        }

        ConstByteArray_t data = {
            .bytes = &commandPayload.bytes[processedBytes],
            .count = segmentDataLength
        };
        processedBytes += segmentDataLength;

        DriveRequest_t request;
        if (!CommWrapper_MotorPorts_Call_CreateDriveRequest(portIdx, data, &request))
        {
            response.bytes[0] = 1u;
            *responseCount = 1u;
            return Comm_Status_Error_CommandError;
        }
        uint32_t primask = __get_PRIMASK();
        __disable_irq();
        CommWrapper_MotorPorts_Write_DriveRequest(portIdx, &request);
        __set_PRIMASK(primask);

        response.bytes[command_index] = request.version;
        command_index++;
    }
    *responseCount = command_index;

    return Comm_Status_Ok;
    /* End User Code Section: Command_SetControlValue_Start:run Start */
    /* Begin User Code Section: Command_SetControlValue_Start:run End */

    /* End User Code Section: Command_SetControlValue_Start:run End */
}

Comm_Status_t CommWrapper_MotorPorts_Run_Command_TestMotorOnPort_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount)
{
    /* Begin User Code Section: Command_TestMotorOnPort_Start:run Start */
    (void) response;
    (void) responseCount;

    if (commandPayload.count != 3)
    {
        return Comm_Status_Error_PayloadLengthError;
    }

    uint8_t port_idx = MOTOR_PORT_IDX(commandPayload.bytes[0]);
    uint8_t test_power = commandPayload.bytes[1];
    uint8_t threshold = commandPayload.bytes[2];

    AsyncOperationState_t status = CommWrapper_MotorPorts_Async_TestMotorOnPort_Call(
        port_idx, test_power, threshold);

    if (status == AsyncOperationState_Started)
    {
        return Comm_Status_Pending;
    }
    else
    {
        return Comm_Status_Error_InternalError;
    }

    /* End User Code Section: Command_TestMotorOnPort_Start:run Start */
    /* Begin User Code Section: Command_TestMotorOnPort_Start:run End */

    /* End User Code Section: Command_TestMotorOnPort_Start:run End */
}

Comm_Status_t CommWrapper_MotorPorts_Run_Command_TestMotorOnPort_GetResult(ByteArray_t response, uint8_t* responseCount)
{
    /* Begin User Code Section: Command_TestMotorOnPort_GetResult:run Start */
    (void) response;
    (void) responseCount;

    bool result;
    switch (CommWrapper_MotorPorts_Async_TestMotorOnPort_GetResult(&result))
    {
        case AsyncOperationState_Done:
            if (result)
            {
                response.bytes[0] = 1;
                *responseCount = 1;
                return Comm_Status_Ok;
            }
            else
            {
                response.bytes[0] = 0;
                *responseCount = 1;
                return Comm_Status_Ok;
            }
            break;

        case AsyncOperationState_Busy:
            return Comm_Status_Pending;

        default:
            return Comm_Status_Error_InternalError;
    }

    /* End User Code Section: Command_TestMotorOnPort_GetResult:run Start */
    /* Begin User Code Section: Command_TestMotorOnPort_GetResult:run End */

    SEGGER_RTT_WriteString(0, "Should never reach this\n");
    /* End User Code Section: Command_TestMotorOnPort_GetResult:run End */
}

__attribute__((weak))
AsyncOperationState_t CommWrapper_MotorPorts_Async_SetPortType_Call(uint8_t port_idx, uint8_t port_type)
{
    (void) port_idx;
    (void) port_type;
    /* Begin User Code Section: SetPortType:async_call Start */

    /* End User Code Section: SetPortType:async_call Start */
    /* Begin User Code Section: SetPortType:async_call End */

    /* End User Code Section: SetPortType:async_call End */
    return AsyncOperationState_Busy;
}

__attribute__((weak))
AsyncOperationState_t CommWrapper_MotorPorts_Async_SetPortType_GetResult(bool* result)
{
    (void) result;
    /* Begin User Code Section: SetPortType:get_result Start */

    /* End User Code Section: SetPortType:get_result Start */
    /* Begin User Code Section: SetPortType:get_result End */

    /* End User Code Section: SetPortType:get_result End */
    return AsyncOperationState_Busy;
}

__attribute__((weak))
void CommWrapper_MotorPorts_Async_SetPortType_Cancel(void)
{
    /* Begin User Code Section: SetPortType:cancel Start */

    /* End User Code Section: SetPortType:cancel Start */
    /* Begin User Code Section: SetPortType:cancel End */

    /* End User Code Section: SetPortType:cancel End */
}

__attribute__((weak))
AsyncOperationState_t CommWrapper_MotorPorts_Async_SetPortConfig_Call(uint8_t port_idx, ByteArray_t configuration)
{
    (void) configuration;
    (void) port_idx;
    /* Begin User Code Section: SetPortConfig:async_call Start */

    /* End User Code Section: SetPortConfig:async_call Start */
    /* Begin User Code Section: SetPortConfig:async_call End */

    /* End User Code Section: SetPortConfig:async_call End */
    return AsyncOperationState_Busy;
}

__attribute__((weak))
AsyncOperationState_t CommWrapper_MotorPorts_Async_SetPortConfig_GetResult(bool* result)
{
    (void) result;
    /* Begin User Code Section: SetPortConfig:get_result Start */

    /* End User Code Section: SetPortConfig:get_result Start */
    /* Begin User Code Section: SetPortConfig:get_result End */

    /* End User Code Section: SetPortConfig:get_result End */
    return AsyncOperationState_Busy;
}

__attribute__((weak))
void CommWrapper_MotorPorts_Async_SetPortConfig_Cancel(void)
{
    /* Begin User Code Section: SetPortConfig:cancel Start */

    /* End User Code Section: SetPortConfig:cancel Start */
    /* Begin User Code Section: SetPortConfig:cancel End */

    /* End User Code Section: SetPortConfig:cancel End */
}

__attribute__((weak))
AsyncOperationState_t CommWrapper_MotorPorts_Async_TestMotorOnPort_Call(uint8_t port_idx, uint8_t test_power, uint8_t threshold)
{
    (void) port_idx;
    (void) test_power;
    (void) threshold;
    /* Begin User Code Section: TestMotorOnPort:async_call Start */

    /* End User Code Section: TestMotorOnPort:async_call Start */
    /* Begin User Code Section: TestMotorOnPort:async_call End */

    /* End User Code Section: TestMotorOnPort:async_call End */
    return AsyncOperationState_Busy;
}

__attribute__((weak))
AsyncOperationState_t CommWrapper_MotorPorts_Async_TestMotorOnPort_GetResult(bool* result)
{
    (void) result;
    /* Begin User Code Section: TestMotorOnPort:get_result Start */

    /* End User Code Section: TestMotorOnPort:get_result Start */
    /* Begin User Code Section: TestMotorOnPort:get_result End */

    /* End User Code Section: TestMotorOnPort:get_result End */
    return AsyncOperationState_Busy;
}

__attribute__((weak))
void CommWrapper_MotorPorts_Async_TestMotorOnPort_Cancel(void)
{
    /* Begin User Code Section: TestMotorOnPort:cancel Start */

    /* End User Code Section: TestMotorOnPort:cancel Start */
    /* Begin User Code Section: TestMotorOnPort:cancel End */

    /* End User Code Section: TestMotorOnPort:cancel End */
}

__attribute__((weak))
void CommWrapper_MotorPorts_Call_ReadPortTypes(ByteArray_t* buffer)
{
    (void) buffer;
    /* Begin User Code Section: ReadPortTypes:run Start */

    /* End User Code Section: ReadPortTypes:run Start */
    /* Begin User Code Section: ReadPortTypes:run End */

    /* End User Code Section: ReadPortTypes:run End */
}

__attribute__((weak))
bool CommWrapper_MotorPorts_Call_CreateDriveRequest(uint8_t port_idx, ConstByteArray_t buffer, DriveRequest_t* request)
{
    (void) buffer;
    (void) port_idx;
    (void) request;
    /* Begin User Code Section: CreateDriveRequest:run Start */

    /* End User Code Section: CreateDriveRequest:run Start */
    /* Begin User Code Section: CreateDriveRequest:run End */

    /* End User Code Section: CreateDriveRequest:run End */
    return false;
}

__attribute__((weak))
void CommWrapper_MotorPorts_Write_DriveRequest(uint32_t index, const DriveRequest_t* value)
{
    ASSERT(index < 6);
    ASSERT(value != NULL);
    /* Begin User Code Section: DriveRequest:write Start */

    /* End User Code Section: DriveRequest:write Start */
    /* Begin User Code Section: DriveRequest:write End */

    /* End User Code Section: DriveRequest:write End */
}

__attribute__((weak))
uint8_t CommWrapper_MotorPorts_Read_PortCount(void)
{
    /* Begin User Code Section: PortCount:read Start */

    /* End User Code Section: PortCount:read Start */
    /* Begin User Code Section: PortCount:read End */

    /* End User Code Section: PortCount:read End */
    return 0u;
}

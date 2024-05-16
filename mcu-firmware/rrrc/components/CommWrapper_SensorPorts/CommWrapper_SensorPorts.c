#include "CommWrapper_SensorPorts.h"
#include "utils.h"

/* Begin User Code Section: Declarations */
#include "utils_assert.h"
#include <string.h>

static uint8_t config_buffer[128];

#define SENSOR_PORT_IDX(x) (x)

#define TEST_SENSOR_ON_PORT_RESULT_ABSENT  0
#define TEST_SENSOR_ON_PORT_RESULT_PRESENT 1
#define TEST_SENSOR_ON_PORT_RESULT_UNKNOWN 2
#define TEST_SENSOR_ON_PORT_RESULT_ERROR   3
/* End User Code Section: Declarations */

Comm_Status_t CommWrapper_SensorPorts_Run_Command_GetPortAmount_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount)
{
    /* Begin User Code Section: Command_GetPortAmount_Start:run Start */
    if (commandPayload.count != 0u)
    {
        return Comm_Status_Error_PayloadLengthError;
    }

    ASSERT(response.count >= 1u);
    response.bytes[0] = CommWrapper_SensorPorts_Read_PortCount();
    *responseCount = 1u;

    return Comm_Status_Ok;
    /* End User Code Section: Command_GetPortAmount_Start:run Start */
    /* Begin User Code Section: Command_GetPortAmount_Start:run End */

    /* End User Code Section: Command_GetPortAmount_Start:run End */
}

Comm_Status_t CommWrapper_SensorPorts_Run_Command_GetPortTypes_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount)
{
    /* Begin User Code Section: Command_GetPortTypes_Start:run Start */
    (void) commandPayload;
    if (commandPayload.count != 0u)
    {
        return Comm_Status_Error_PayloadLengthError;
    }

    CommWrapper_SensorPorts_Call_ReadPortTypes(&response);
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

Comm_Status_t CommWrapper_SensorPorts_Run_Command_SetPortType_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount)
{
    /* Begin User Code Section: Command_SetPortType_Start:run Start */
    (void) response;
    (void) responseCount;

    if (commandPayload.count != 2u)
    {
        return Comm_Status_Error_PayloadLengthError;
    }

    uint8_t port_idx = SENSOR_PORT_IDX(commandPayload.bytes[0]);
    uint8_t port_type = commandPayload.bytes[1];

    if (CommWrapper_SensorPorts_Async_SetPortType_Call(port_idx, port_type) == AsyncOperationState_Started)
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

Comm_Status_t CommWrapper_SensorPorts_Run_Command_SetPortType_GetResult(ByteArray_t response, uint8_t* responseCount)
{
    /* Begin User Code Section: Command_SetPortType_GetResult:run Start */
    bool result = false;
    switch (CommWrapper_SensorPorts_Async_SetPortType_GetResult(&result))
    {
        case AsyncOperationState_Done:
            response.bytes[0] = (uint8_t)result;
            *responseCount = 1u;
            return Comm_Status_Ok;

        case AsyncOperationState_Busy:
            return Comm_Status_Pending;

        default:
            return Comm_Status_Error_InternalError;
    }

    /* End User Code Section: Command_SetPortType_GetResult:run Start */
    /* Begin User Code Section: Command_SetPortType_GetResult:run End */

    /* End User Code Section: Command_SetPortType_GetResult:run End */
}

Comm_Status_t CommWrapper_SensorPorts_Run_Command_SetPortConfig_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount)
{
    /* Begin User Code Section: Command_SetPortConfig_Start:run Start */
    (void) response;
    (void) responseCount;

    if (commandPayload.count == 0u || commandPayload.count > ARRAY_SIZE(config_buffer) + 1u)
    {
        return Comm_Status_Error_PayloadLengthError;
    }

    uint8_t port_idx = SENSOR_PORT_IDX(commandPayload.bytes[0]);
    memcpy(config_buffer, &commandPayload.bytes[1], commandPayload.count - 1u);

    ByteArray_t config = {
        .bytes = config_buffer,
        .count = commandPayload.count - 1u
    };
    if (CommWrapper_SensorPorts_Async_SetPortConfig_Call(port_idx, config) == AsyncOperationState_Started)
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

Comm_Status_t CommWrapper_SensorPorts_Run_Command_SetPortConfig_GetResult(ByteArray_t response, uint8_t* responseCount)
{
    /* Begin User Code Section: Command_SetPortConfig_GetResult:run Start */
    (void) response;
    (void) responseCount;

    bool result;
    switch (CommWrapper_SensorPorts_Async_SetPortConfig_GetResult(&result))
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

Comm_Status_t CommWrapper_SensorPorts_Run_Command_ReadSensorInfo_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount)
{
    /* Begin User Code Section: Command_ReadSensorInfo_Start:run Start */
    uint8_t page;

    if (commandPayload.count == 1u)
    {
        page = 0u;
    }
    else if (commandPayload.count == 2u)
    {
        page = commandPayload.bytes[1];
    }
    else
    {
        return Comm_Status_Error_PayloadLengthError;
    }

    CommWrapper_SensorPorts_Call_ReadSensorInfo(SENSOR_PORT_IDX(commandPayload.bytes[0]), page, &response);
    if (responseCount != NULL)
    {
        *responseCount = response.count;
    }

    return Comm_Status_Ok;
    /* End User Code Section: Command_ReadSensorInfo_Start:run Start */
    /* Begin User Code Section: Command_ReadSensorInfo_Start:run End */

    /* End User Code Section: Command_ReadSensorInfo_Start:run End */
}

Comm_Status_t CommWrapper_SensorPorts_Run_Command_TestSensorOnPort_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount)
{
    /* Begin User Code Section: Command_TestSensorOnPort_Start:run Start */
    (void) response;
    (void) responseCount;

    if (commandPayload.count != 2)
    {
        return Comm_Status_Error_PayloadLengthError;
    }

    uint8_t port_idx = SENSOR_PORT_IDX(commandPayload.bytes[0]);
    uint8_t port_type = commandPayload.bytes[1];

    if (CommWrapper_SensorPorts_Async_TestSensorOnPort_Call(port_idx, port_type) == AsyncOperationState_Started)
    {
        return Comm_Status_Pending;
    }
    else
    {
        return Comm_Status_Error_InternalError;
    }
    return Comm_Status_Ok;

    /* End User Code Section: Command_TestSensorOnPort_Start:run Start */
    /* Begin User Code Section: Command_TestSensorOnPort_Start:run End */

    /* End User Code Section: Command_TestSensorOnPort_Start:run End */
}

Comm_Status_t CommWrapper_SensorPorts_Run_Command_TestSensorOnPort_GetResult(ByteArray_t response, uint8_t* responseCount)
{
    /* Begin User Code Section: Command_TestSensorOnPort_GetResult:run Start */
    TestSensorOnPortResult_t result;

    switch (CommWrapper_SensorPorts_Async_TestSensorOnPort_GetResult(&result))
    {
        case AsyncOperationState_Done:
            *responseCount = 1u;
            if (result == TestSensorOnPortResult_NotPresent)
            {
                response.bytes[0] = TEST_SENSOR_ON_PORT_RESULT_ABSENT;
                return Comm_Status_Ok;
            }
            else if (result == TestSensorOnPortResult_Present)
            {
                response.bytes[0] = TEST_SENSOR_ON_PORT_RESULT_PRESENT;
                return Comm_Status_Ok;
            }
            else if (result == TestSensorOnPortResult_Unknown)
            {
                response.bytes[0] = TEST_SENSOR_ON_PORT_RESULT_UNKNOWN;
                return Comm_Status_Ok;
            }
            else
            {
                response.bytes[0] = TEST_SENSOR_ON_PORT_RESULT_ERROR;
                return Comm_Status_Error_CommandError;
            }
            break;

        case AsyncOperationState_Busy:
            return Comm_Status_Pending;

        default:
            return Comm_Status_Error_InternalError;
    }

    /* End User Code Section: Command_TestSensorOnPort_GetResult:run Start */
    /* Begin User Code Section: Command_TestSensorOnPort_GetResult:run End */

    /* End User Code Section: Command_TestSensorOnPort_GetResult:run End */
}

__attribute__((weak))
AsyncOperationState_t CommWrapper_SensorPorts_Async_TestSensorOnPort_Call(uint8_t port_idx, uint8_t port_type)
{
    (void) port_idx;
    (void) port_type;
    /* Begin User Code Section: TestSensorOnPort:async_call Start */

    /* End User Code Section: TestSensorOnPort:async_call Start */
    /* Begin User Code Section: TestSensorOnPort:async_call End */

    /* End User Code Section: TestSensorOnPort:async_call End */
    return AsyncOperationState_Busy;
}

__attribute__((weak))
AsyncOperationState_t CommWrapper_SensorPorts_Async_TestSensorOnPort_GetResult(TestSensorOnPortResult_t* result)
{
    (void) result;
    /* Begin User Code Section: TestSensorOnPort:get_result Start */

    /* End User Code Section: TestSensorOnPort:get_result Start */
    /* Begin User Code Section: TestSensorOnPort:get_result End */

    /* End User Code Section: TestSensorOnPort:get_result End */
    return AsyncOperationState_Busy;
}

__attribute__((weak))
void CommWrapper_SensorPorts_Async_TestSensorOnPort_Cancel(void)
{
    /* Begin User Code Section: TestSensorOnPort:cancel Start */

    /* End User Code Section: TestSensorOnPort:cancel Start */
    /* Begin User Code Section: TestSensorOnPort:cancel End */

    /* End User Code Section: TestSensorOnPort:cancel End */
}

__attribute__((weak))
AsyncOperationState_t CommWrapper_SensorPorts_Async_SetPortType_Call(uint8_t port_idx, uint8_t port_type)
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
AsyncOperationState_t CommWrapper_SensorPorts_Async_SetPortType_GetResult(bool* result)
{
    (void) result;
    /* Begin User Code Section: SetPortType:get_result Start */

    /* End User Code Section: SetPortType:get_result Start */
    /* Begin User Code Section: SetPortType:get_result End */

    /* End User Code Section: SetPortType:get_result End */
    return AsyncOperationState_Busy;
}

__attribute__((weak))
void CommWrapper_SensorPorts_Async_SetPortType_Cancel(void)
{
    /* Begin User Code Section: SetPortType:cancel Start */

    /* End User Code Section: SetPortType:cancel Start */
    /* Begin User Code Section: SetPortType:cancel End */

    /* End User Code Section: SetPortType:cancel End */
}

__attribute__((weak))
AsyncOperationState_t CommWrapper_SensorPorts_Async_SetPortConfig_Call(uint8_t port_idx, ByteArray_t configuration)
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
AsyncOperationState_t CommWrapper_SensorPorts_Async_SetPortConfig_GetResult(bool* result)
{
    (void) result;
    /* Begin User Code Section: SetPortConfig:get_result Start */

    /* End User Code Section: SetPortConfig:get_result Start */
    /* Begin User Code Section: SetPortConfig:get_result End */

    /* End User Code Section: SetPortConfig:get_result End */
    return AsyncOperationState_Busy;
}

__attribute__((weak))
void CommWrapper_SensorPorts_Async_SetPortConfig_Cancel(void)
{
    /* Begin User Code Section: SetPortConfig:cancel Start */

    /* End User Code Section: SetPortConfig:cancel Start */
    /* Begin User Code Section: SetPortConfig:cancel End */

    /* End User Code Section: SetPortConfig:cancel End */
}

__attribute__((weak))
void CommWrapper_SensorPorts_Call_ReadPortTypes(ByteArray_t* buffer)
{
    (void) buffer;
    /* Begin User Code Section: ReadPortTypes:run Start */

    /* End User Code Section: ReadPortTypes:run Start */
    /* Begin User Code Section: ReadPortTypes:run End */

    /* End User Code Section: ReadPortTypes:run End */
}

__attribute__((weak))
void CommWrapper_SensorPorts_Call_ReadSensorInfo(uint8_t port_idx, uint8_t page, ByteArray_t* buffer)
{
    (void) buffer;
    (void) page;
    (void) port_idx;
    /* Begin User Code Section: ReadSensorInfo:run Start */

    /* End User Code Section: ReadSensorInfo:run Start */
    /* Begin User Code Section: ReadSensorInfo:run End */

    /* End User Code Section: ReadSensorInfo:run End */
}

__attribute__((weak))
uint8_t CommWrapper_SensorPorts_Read_PortCount(void)
{
    /* Begin User Code Section: PortCount:read Start */

    /* End User Code Section: PortCount:read Start */
    /* Begin User Code Section: PortCount:read End */

    /* End User Code Section: PortCount:read End */
    return 0u;
}

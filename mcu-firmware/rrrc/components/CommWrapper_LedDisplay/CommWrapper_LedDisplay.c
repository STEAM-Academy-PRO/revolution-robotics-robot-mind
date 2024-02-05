#include "CommWrapper_LedDisplay.h"
#include "utils.h"
#include "utils_assert.h"

/* Begin User Code Section: Declarations */

/* End User Code Section: Declarations */

void CommWrapper_LedDisplay_Run_Reset(void)
{
    /* Begin User Code Section: Reset:run Start */
    CommWrapper_LedDisplay_Write_Scenario(RingLedScenario_BreathingGreen);
    /* End User Code Section: Reset:run Start */
    /* Begin User Code Section: Reset:run End */

    /* End User Code Section: Reset:run End */
}

Comm_Status_t CommWrapper_LedDisplay_Run_Command_GetScenarioTypes_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount)
{
    /* Begin User Code Section: Command_GetScenarioTypes_Start:run Start */
    if (commandPayload.count != 0u)
    {
        return Comm_Status_Error_PayloadLengthError;
    }

    uint32_t len = 0u;
    for (uint32_t i = 0u; i < CommWrapper_LedDisplay_Read_ScenarioCount(); i++)
    {
        ASSERT (len < response.count);

        // 2 bytes offset to store index and name_length
        ByteArray_t destination = {
            .bytes = &response.bytes[len + 2u],
            .count = response.count - len - 2u
        };

        ssize_t name_length = CommWrapper_LedDisplay_Call_ReadScenarioName(i, destination);
        if (name_length == 0)
        {
            /* scenario has no name, skip it */
            continue;
        }
        else if (name_length < 0)
        {
            // Handles:
            // if (name_length == -1): buffer full
            // if (name_length == -2): scenario not found
            // if (name_length < -2): any other error
            *responseCount = 0u;
            return Comm_Status_Error_InternalError;
        }

        response.bytes[len] = i;
        response.bytes[len + 1] = name_length;

        len = len + 2 + name_length;
    }
    *responseCount = len;

    return Comm_Status_Ok;
    /* End User Code Section: Command_GetScenarioTypes_Start:run Start */
    /* Begin User Code Section: Command_GetScenarioTypes_Start:run End */

    /* End User Code Section: Command_GetScenarioTypes_Start:run End */
}

Comm_Status_t CommWrapper_LedDisplay_Run_Command_SetScenarioType_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount)
{
    /* Begin User Code Section: Command_SetScenarioType_Start:run Start */
    if (commandPayload.count != 1u)
    {
        return Comm_Status_Error_PayloadLengthError;
    }

    uint8_t idx = commandPayload.bytes[0];
    if (idx >= CommWrapper_LedDisplay_Read_ScenarioCount())
    {
        response.bytes[0] = idx;
        *responseCount = 1u;
        return Comm_Status_Error_CommandError;
    }

    CommWrapper_LedDisplay_Write_Scenario((RingLedScenario_t) idx);

    return Comm_Status_Ok;
    /* End User Code Section: Command_SetScenarioType_Start:run Start */
    /* Begin User Code Section: Command_SetScenarioType_Start:run End */

    /* End User Code Section: Command_SetScenarioType_Start:run End */
}

Comm_Status_t CommWrapper_LedDisplay_Run_Command_GetRingLedAmount_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount)
{
    /* Begin User Code Section: Command_GetRingLedAmount_Start:run Start */
    if (commandPayload.count != 0u)
    {
        return Comm_Status_Error_PayloadLengthError;
    }

    ASSERT(response.count >= 1u);

    response.bytes[0] = 12u;
    *responseCount = 1u;

    return Comm_Status_Ok;
    /* End User Code Section: Command_GetRingLedAmount_Start:run Start */
    /* Begin User Code Section: Command_GetRingLedAmount_Start:run End */

    /* End User Code Section: Command_GetRingLedAmount_Start:run End */
}

Comm_Status_t CommWrapper_LedDisplay_Run_Command_SetUserFrame_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount)
{
    /* Begin User Code Section: Command_SetUserFrame_Start:run Start */
    (void) response;
    (void) responseCount;

    if (commandPayload.count != 12u * sizeof(rgb565_t))
    {
        return Comm_Status_Error_PayloadLengthError;
    }

    for (uint32_t i = 0u; i < 12u; i++)
    {
        uint16_t c = commandPayload.bytes[2 * i] | (commandPayload.bytes[2 * i + 1] << 8u);
        rgb565_t color = {
            .R = (c & 0xF800u) >> 11u,
            .G = (c & 0x07E0u) >>  5u,
            .B = (c & 0x001Fu) >>  0u
        };
        uint32_t primask = __get_PRIMASK();
        __disable_irq();
        CommWrapper_LedDisplay_Write_UserFrame(i, rgb565_to_rgb(color));
        __set_PRIMASK(primask);
    }

    return Comm_Status_Ok;
    /* End User Code Section: Command_SetUserFrame_Start:run Start */
    /* Begin User Code Section: Command_SetUserFrame_Start:run End */

    /* End User Code Section: Command_SetUserFrame_Start:run End */
}

__attribute__((weak))
ssize_t CommWrapper_LedDisplay_Call_ReadScenarioName(RingLedScenario_t scenario, ByteArray_t destination)
{
    (void) destination;
    (void) scenario;
    /* Begin User Code Section: ReadScenarioName:run Start */

    /* End User Code Section: ReadScenarioName:run Start */
    /* Begin User Code Section: ReadScenarioName:run End */

    /* End User Code Section: ReadScenarioName:run End */
    return 0;
}

__attribute__((weak))
void CommWrapper_LedDisplay_Write_Scenario(RingLedScenario_t value)
{
    (void) value;
    /* Begin User Code Section: Scenario:write Start */

    /* End User Code Section: Scenario:write Start */
    /* Begin User Code Section: Scenario:write End */

    /* End User Code Section: Scenario:write End */
}

__attribute__((weak))
void CommWrapper_LedDisplay_Write_UserFrame(uint32_t index, rgb_t value)
{
    (void) value;
    ASSERT(index < 12);
    /* Begin User Code Section: UserFrame:write Start */

    /* End User Code Section: UserFrame:write Start */
    /* Begin User Code Section: UserFrame:write End */

    /* End User Code Section: UserFrame:write End */
}

__attribute__((weak))
size_t CommWrapper_LedDisplay_Read_ScenarioCount(void)
{
    /* Begin User Code Section: ScenarioCount:read Start */

    /* End User Code Section: ScenarioCount:read Start */
    /* Begin User Code Section: ScenarioCount:read End */

    /* End User Code Section: ScenarioCount:read End */
    return 0;
}

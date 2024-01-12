#include "CommWrapper_McuStatusCollector.h"
#include "utils.h"

/* Begin User Code Section: Declarations */

/* End User Code Section: Declarations */

Comm_Status_t CommWrapper_McuStatusCollector_Run_Command_Reset_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount)
{
    /* Begin User Code Section: Command_Reset_Start:run Start */
    (void) response;
    (void) responseCount;

    if (commandPayload.count != 0u)
    {
        return Comm_Status_Error_PayloadLengthError;
    }

    CommWrapper_McuStatusCollector_Call_ResetSlots();

    return Comm_Status_Ok;
    /* End User Code Section: Command_Reset_Start:run Start */
    /* Begin User Code Section: Command_Reset_Start:run End */

    /* End User Code Section: Command_Reset_Start:run End */
}

Comm_Status_t CommWrapper_McuStatusCollector_Run_Command_ControlSlot_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount)
{
    /* Begin User Code Section: Command_ControlSlot_Start:run Start */
    (void) response;
    (void) responseCount;

    if (commandPayload.count != 2u)
    {
        return Comm_Status_Error_PayloadLengthError;
    }

    uint8_t slot = commandPayload.bytes[0];
    uint8_t state = commandPayload.bytes[1];
    if (slot > 31u || state > 1u)
    {
        return Comm_Status_Error_CommandError;
    }

    if (state)
    {
        CommWrapper_McuStatusCollector_Call_EnableSlot(slot);
    }
    else
    {
        CommWrapper_McuStatusCollector_Call_DisableSlot(slot);
    }

    return Comm_Status_Ok;
    /* End User Code Section: Command_ControlSlot_Start:run Start */
    /* Begin User Code Section: Command_ControlSlot_Start:run End */

    /* End User Code Section: Command_ControlSlot_Start:run End */
}

Comm_Status_t CommWrapper_McuStatusCollector_Run_Command_ReadStatus_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount)
{
    /* Begin User Code Section: Command_ReadStatus_Start:run Start */
    if (commandPayload.count != 0u)
    {
        return Comm_Status_Error_PayloadLengthError;
    }

    *responseCount = CommWrapper_McuStatusCollector_Call_Read(response);

    return Comm_Status_Ok;
    /* End User Code Section: Command_ReadStatus_Start:run Start */
    /* Begin User Code Section: Command_ReadStatus_Start:run End */

    /* End User Code Section: Command_ReadStatus_Start:run End */
}

__attribute__((weak))
uint8_t CommWrapper_McuStatusCollector_Call_Read(ByteArray_t destination)
{
    (void) destination;
    /* Begin User Code Section: Read:run Start */

    /* End User Code Section: Read:run Start */
    /* Begin User Code Section: Read:run End */

    /* End User Code Section: Read:run End */
    return 0u;
}

__attribute__((weak))
void CommWrapper_McuStatusCollector_Call_ResetSlots(void)
{
    /* Begin User Code Section: ResetSlots:run Start */

    /* End User Code Section: ResetSlots:run Start */
    /* Begin User Code Section: ResetSlots:run End */

    /* End User Code Section: ResetSlots:run End */
}

__attribute__((weak))
void CommWrapper_McuStatusCollector_Call_EnableSlot(uint8_t slot)
{
    (void) slot;
    /* Begin User Code Section: EnableSlot:run Start */

    /* End User Code Section: EnableSlot:run Start */
    /* Begin User Code Section: EnableSlot:run End */

    /* End User Code Section: EnableSlot:run End */
}

__attribute__((weak))
void CommWrapper_McuStatusCollector_Call_DisableSlot(uint8_t slot)
{
    (void) slot;
    /* Begin User Code Section: DisableSlot:run Start */

    /* End User Code Section: DisableSlot:run Start */
    /* Begin User Code Section: DisableSlot:run End */

    /* End User Code Section: DisableSlot:run End */
}

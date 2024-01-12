#include "MasterCommunication.h"
#include "utils.h"

/* Begin User Code Section: Declarations */
#include "CommunicationManager.h"

static uint8_t responseBuffer[256];

static Comm_ResponseHeader_t defaultResponse =
{
    .status = Comm_Status_Busy,
    .payloadLength = 0u,
    .payloadChecksum = 0xFFFFu
};

static Comm_ResponseHeader_t longRxErrorResponse =
{
    .status = Comm_Status_Error_PayloadLengthError,
    .payloadLength = 0u,
    .payloadChecksum = 0xFFFFu
};
/* End User Code Section: Declarations */

void MasterCommunication_Run_OnInit(const Comm_CommandHandler_t* commandTable, size_t commandTableSize)
{
    /* Begin User Code Section: OnInit:run Start */
    Comm_ProtectMessageHeader(&defaultResponse);
    Comm_ProtectMessageHeader(&longRxErrorResponse);

    Comm_Init(commandTable, commandTableSize);
    /* End User Code Section: OnInit:run Start */
    /* Begin User Code Section: OnInit:run End */

    /* End User Code Section: OnInit:run End */
}

void MasterCommunication_Run_HandleCommand(ConstByteArray_t message)
{
    /* Begin User Code Section: HandleCommand:run Start */
    const Comm_Command_t* command = (const Comm_Command_t*) message.bytes;

    size_t responseCount;
    Comm_Response_t* response = (Comm_Response_t*) responseBuffer;

    if (sizeof(Comm_CommandHeader_t) + command->header.payloadLength != message.count)
    {
        response->header.status = Comm_Status_Error_PayloadLengthError;
        response->header.payloadLength = 0u;
        responseCount = sizeof(Comm_ResponseHeader_t);
    }
    else
    {
        responseCount = Comm_Handle(command, response, sizeof(responseBuffer));
    }

    Comm_Protect(response);
    MasterCommunication_Call_SendResponse((ConstByteArray_t) {
        .bytes = responseBuffer,
        .count = responseCount
    });
    /* End User Code Section: HandleCommand:run Start */
    /* Begin User Code Section: HandleCommand:run End */

    /* End User Code Section: HandleCommand:run End */
}

ConstByteArray_t MasterCommunication_Constant_DefaultResponse(void)
{
    /* Begin User Code Section: DefaultResponse:constant Start */

    /* End User Code Section: DefaultResponse:constant Start */
    /* Begin User Code Section: DefaultResponse:constant End */

    /* End User Code Section: DefaultResponse:constant End */
    return (ConstByteArray_t) { .bytes = (uint8_t*) &defaultResponse, .count = sizeof(defaultResponse) };
}

ConstByteArray_t MasterCommunication_Constant_LongRxErrorResponse(void)
{
    /* Begin User Code Section: LongRxErrorResponse:constant Start */

    /* End User Code Section: LongRxErrorResponse:constant Start */
    /* Begin User Code Section: LongRxErrorResponse:constant End */

    /* End User Code Section: LongRxErrorResponse:constant End */
    return (ConstByteArray_t) { .bytes = (uint8_t*) &longRxErrorResponse, .count = sizeof(longRxErrorResponse) };
}

__attribute__((weak))
void MasterCommunication_Call_SendResponse(ConstByteArray_t response)
{
    (void) response;
    /* Begin User Code Section: SendResponse:run Start */

    /* End User Code Section: SendResponse:run Start */
    /* Begin User Code Section: SendResponse:run End */

    /* End User Code Section: SendResponse:run End */
}

__attribute__((weak))
uint8_t MasterCommunication_Call_Calculate_CRC7(uint8_t init_value, ConstByteArray_t data)
{
    (void) data;
    (void) init_value;
    /* Begin User Code Section: Calculate_CRC7:run Start */

    /* End User Code Section: Calculate_CRC7:run Start */
    /* Begin User Code Section: Calculate_CRC7:run End */

    /* End User Code Section: Calculate_CRC7:run End */
    return 0u;
}

__attribute__((weak))
uint16_t MasterCommunication_Call_Calculate_CRC16(uint16_t init_value, ConstByteArray_t data)
{
    (void) data;
    (void) init_value;
    /* Begin User Code Section: Calculate_CRC16:run Start */

    /* End User Code Section: Calculate_CRC16:run Start */
    /* Begin User Code Section: Calculate_CRC16:run End */

    /* End User Code Section: Calculate_CRC16:run End */
    return 0u;
}

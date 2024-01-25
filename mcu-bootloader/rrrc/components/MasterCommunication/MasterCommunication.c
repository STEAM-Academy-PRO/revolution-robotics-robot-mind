#include "MasterCommunication.h"
#include "../../utils/crc.h"

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

void MasterCommunication_Run_GetDefaultResponse(uint8_t** defaultResponseBuffer, size_t* defaultResponseLength)
{
    *defaultResponseBuffer = (uint8_t*) &defaultResponse;
    *defaultResponseLength = sizeof(defaultResponse);
}

void MasterCommunication_Run_GetLongRxErrorResponse(uint8_t** longRxErrorResponseBuffer, size_t* longRxErrorResponseLength)
{
    *longRxErrorResponseBuffer = (uint8_t*) &longRxErrorResponse;
    *longRxErrorResponseLength = sizeof(longRxErrorResponse);
}

void MasterCommunication_Run_OnInit(const Comm_CommandHandler_t* commandTable, size_t commandTableSize)
{
    Comm_ProtectMessageHeader(&defaultResponse);
    Comm_ProtectMessageHeader(&longRxErrorResponse);

    Comm_Init(commandTable, commandTableSize);
}

void MasterCommunication_Run_HandleCommand(const uint8_t* buffer, size_t bufferSize)
{
    const Comm_Command_t* command = (const Comm_Command_t*) buffer;

    size_t responseCount;
    Comm_Response_t* response = (Comm_Response_t*) responseBuffer;

    if (sizeof(Comm_CommandHeader_t) + command->header.payloadLength != bufferSize)
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
    MasterCommunication_Call_SendResponse(&responseBuffer[0], responseCount);
}

__attribute__((weak))
void MasterCommunication_Call_SendResponse(const uint8_t* responseBuffer, size_t responseSize)
{
    /* nothing to do */
}

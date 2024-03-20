#include "CommunicationManager.h"
#include "utils_assert.h"

#include <stdbool.h>
#include "SEGGER_RTT.h"

#include "utils/crc.h"
#include "comm_handlers.h"

static bool _commandValid(const Comm_Command_t* command)
{
    uint8_t headerChecksum = CRC7_Calculate(0xFFu, (uint8_t*) &command->header, sizeof(Comm_CommandHeader_t) - sizeof(uint8_t));

    return command->header.headerChecksum == headerChecksum;
}

static bool _payloadValid(const Comm_Command_t* command)
{
    uint16_t payloadChecksum = CRC16_Calculate(0xFFFFu, command->payload, command->header.payloadLength);

    return command->header.payloadChecksum == payloadChecksum;
}

static Comm_Status_t _handleOperation_GetResult(const Comm_Command_t* command, uint8_t* responseBuffer, uint8_t payloadBufferSize, uint8_t* responseLength)
{
    if (communicationHandlers[command->header.command].GetResult == NULL)
    {
        return Comm_Status_Error_InternalError;
    }
    else
    {
        return communicationHandlers[command->header.command].GetResult(responseBuffer, payloadBufferSize, responseLength);
    }
}

static Comm_Status_t _handleOperation_Start(const Comm_Command_t* command, uint8_t* responseBuffer, uint8_t payloadBufferSize, uint8_t* responseLength)
{
    Comm_Status_t resultStatus = communicationHandlers[command->header.command].Start((const uint8_t*) command->payload, command->header.payloadLength, responseBuffer, payloadBufferSize, responseLength);
    if (resultStatus == Comm_Status_Pending)
    {
        return _handleOperation_GetResult(command, responseBuffer, payloadBufferSize, responseLength);
    }
    else
    {
        return resultStatus;
    }
}

/**
 * Handle a request and prepare a response
 *
 * @return the response length in bytes
 */
size_t Comm_Handle(const Comm_Command_t* command, Comm_Response_t* response, size_t responseBufferSize)
{
    const size_t responseHeaderSize = sizeof(Comm_ResponseHeader_t);

    ASSERT(responseBufferSize > responseHeaderSize);
    ASSERT((responseBufferSize - responseHeaderSize) < 256u); /* protocol limitation */
    uint8_t payloadBufferSize = responseBufferSize - responseHeaderSize;
    uint8_t payloadSize = 0u;
    Comm_Status_t resultStatus;

    if (!_commandValid(command))
    {
        SEGGER_RTT_printf(0, "Command integrity error\n");
        resultStatus = Comm_Status_Error_CommandIntegrityError;
    }
    else if (!_payloadValid(command))
    {
        SEGGER_RTT_printf(0, "Payload integrity error\n");
        resultStatus = Comm_Status_Error_PayloadIntegrityError;
    }
    else if (command->header.command >= COMM_HANDLER_COUNT || communicationHandlers[command->header.command].Start == NULL)
    {
        SEGGER_RTT_printf(0, "Unknown/unimplemented command\n");
        resultStatus = Comm_Status_Error_UnknownCommand;
    }
    else
    {
        switch (command->header.operation)
        {
            case Comm_Operation_Start:
                resultStatus = _handleOperation_Start(command, (uint8_t*) response->payload, payloadBufferSize, &payloadSize);
                break;

            case Comm_Operation_GetResult:
                resultStatus = _handleOperation_GetResult(command, (uint8_t*) response->payload, payloadBufferSize, &payloadSize);
                break;

            default:
                SEGGER_RTT_printf(0, "Unknown operation %d\n", command->header.operation);
                resultStatus = Comm_Status_Error_UnknownOperation;
                break;
        }
    }

    /* detect overwrite */
    if (payloadSize > payloadBufferSize)
    {
        resultStatus = Comm_Status_Error_InternalError;
    }

    /* only certain responses may contain a payload */
    if (resultStatus != Comm_Status_Ok && resultStatus != Comm_Status_Error_CommandError)
    {
        payloadSize = 0u;
    }

    /* fill header */
    response->header.status = resultStatus;
    response->header.payloadLength = payloadSize;

    return payloadSize + responseHeaderSize;
}

void Comm_Protect(Comm_Response_t* response)
{
    response->header.payloadChecksum = CRC16_Calculate(0xFFFFu, (const uint8_t*) response->payload, response->header.payloadLength);
    Comm_ProtectMessageHeader(&response->header);
}

void Comm_ProtectMessageHeader(Comm_ResponseHeader_t* header)
{
    header->headerChecksum = CRC7_Calculate(0xFFu, (uint8_t*) header, sizeof(Comm_ResponseHeader_t) - sizeof(uint8_t));
}

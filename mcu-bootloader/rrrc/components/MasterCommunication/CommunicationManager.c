#include "CommunicationManager.h"
#include "utils_assert.h"
#include "SEGGER_RTT.h"
#include "utils/crc.h"
#include <stdbool.h>

static const Comm_CommandHandler_t* comm_commandTable = NULL;
static size_t comm_commandTableSize = 0u;

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

void Comm_Init(const Comm_CommandHandler_t* commandTable, size_t commandTableSize)
{
    ASSERT(commandTable);

    if (comm_commandTable != NULL)
    {
        for (size_t i = 0u; i < comm_commandTableSize; i++)
        {
            comm_commandTable[i].Cancel();
        }
    }

    comm_commandTable     = commandTable;
    comm_commandTableSize = commandTableSize;
}

static Comm_Status_t _handleOperation_Cancel(const Comm_Command_t* command)
{
    if (comm_commandTable[command->header.command].Cancel != NULL)
    {
        comm_commandTable[command->header.command].Cancel();
    }

    return Comm_Status_Ok;
}

static Comm_Status_t _handleOperation_GetResult(const Comm_Command_t* command, uint8_t* responseBuffer, uint8_t payloadBufferSize, uint8_t* responseLength)
{
    if (comm_commandTable[command->header.command].GetResult == NULL)
    {
        return Comm_Status_Error_InternalError;
    }
    else
    {
        return comm_commandTable[command->header.command].GetResult(responseBuffer, payloadBufferSize, responseLength);
    }
}

static Comm_Status_t _handleOperation_Start(const Comm_Command_t* command, uint8_t* responseBuffer, uint8_t payloadBufferSize, uint8_t* responseLength)
{
    Comm_Status_t resultStatus = comm_commandTable[command->header.command].Start((const uint8_t*) command->payload, command->header.payloadLength, responseBuffer, payloadBufferSize, responseLength);
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
    else if (command->header.command >= comm_commandTableSize || comm_commandTable[command->header.command].Start == NULL)
    {
        SEGGER_RTT_printf(0, "Unknown/unimplemented command\n");
        resultStatus = Comm_Status_Error_UnknownCommand;
    }
    else
    {
        switch (command->header.operation)
        {
            case Comm_Operation_Cancel:
                resultStatus = _handleOperation_Cancel(command);
                break;

            case Comm_Operation_Start:
                resultStatus = _handleOperation_Start(command, (uint8_t*) response->payload, payloadBufferSize, &payloadSize);
                break;

            case Comm_Operation_Restart:
                (void) _handleOperation_Cancel(command);
                resultStatus = _handleOperation_Start(command, (uint8_t*) response->payload, payloadBufferSize, &payloadSize);
                break;

            case Comm_Operation_GetResult:
                resultStatus = _handleOperation_GetResult(command, (uint8_t*) response->payload, payloadBufferSize, &payloadSize);
                break;

            default:
                SEGGER_RTT_printf(0, "Unknown operation\n");
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

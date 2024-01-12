#include "CommunicationManager.h"
#include "utils_assert.h"

#include <stdbool.h>

static const Comm_CommandHandler_t* comm_commandTable = NULL;
static size_t comm_commandTableSize = 0u;

static bool _commandValid(const Comm_Command_t* command)
{
    ConstByteArray_t array = { .bytes = (const uint8_t*) &command->header, .count = sizeof(Comm_CommandHeader_t) - sizeof(uint8_t) };
    uint8_t headerChecksum = MasterCommunication_Call_Calculate_CRC7(0xFFu, array);

    return command->header.headerChecksum == headerChecksum;
}

static bool _payloadValid(const Comm_Command_t* command)
{
    ConstByteArray_t array = { .bytes = command->payload, .count = command->header.payloadLength };
    uint16_t payloadChecksum = MasterCommunication_Call_Calculate_CRC16(0xFFFFu, array);

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

static Comm_Status_t _handleOperation_GetResult(const Comm_Command_t* command, ByteArray_t response, uint8_t* responseLength)
{
    if (comm_commandTable[command->header.command].GetResult == NULL)
    {
        return Comm_Status_Error_InternalError;
    }
    else
    {
        return comm_commandTable[command->header.command].GetResult(response, responseLength);
    }
}

static Comm_Status_t _handleOperation_Start(const Comm_Command_t* command, ByteArray_t response, uint8_t* responseLength)
{
    ConstByteArray_t commandArray = {
        .bytes = command->payload,
        .count = command->header.payloadLength
    };
    Comm_Status_t resultStatus = comm_commandTable[command->header.command].Start(commandArray, response, responseLength);
    if (resultStatus == Comm_Status_Pending)
    {
        return _handleOperation_GetResult(command, response, responseLength);
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
        resultStatus = Comm_Status_Error_CommandIntegrityError;
    }
    else if (!_payloadValid(command))
    {
        resultStatus = Comm_Status_Error_PayloadIntegrityError;
    }
    else if (command->header.command >= comm_commandTableSize || comm_commandTable[command->header.command].Start == NULL)
    {
        /* unimplemented command */
        resultStatus = Comm_Status_Error_UnknownCommand;
    }
    else
    {
        ByteArray_t responseArray = {
            .bytes = (uint8_t*) response->payload,
            .count = payloadBufferSize
        };
        switch (command->header.operation)
        {
            case Comm_Operation_Start:
                resultStatus = _handleOperation_Start(command, responseArray, &payloadSize);
                break;

            case Comm_Operation_GetResult:
                resultStatus = _handleOperation_GetResult(command, responseArray, &payloadSize);
                break;

            case Comm_Operation_Cancel:
                resultStatus = _handleOperation_Cancel(command);
                break;

            case Comm_Operation_Restart:
                (void) _handleOperation_Cancel(command);
                resultStatus = _handleOperation_Start(command, responseArray, &payloadSize);
                break;

            default:
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
    ConstByteArray_t array = { .bytes = response->payload, .count = response->header.payloadLength };
    response->header.payloadChecksum = MasterCommunication_Call_Calculate_CRC16(0xFFFFu, array);
    Comm_ProtectMessageHeader(&response->header);
}

void Comm_ProtectMessageHeader(Comm_ResponseHeader_t* header)
{
    ConstByteArray_t array = { .bytes = (const uint8_t*) header, .count = sizeof(Comm_ResponseHeader_t) - sizeof(uint8_t) };
    header->headerChecksum = MasterCommunication_Call_Calculate_CRC7(0xFFu, array);
}

#include "CommunicationManager.h"
#include "utils_assert.h"

#include <stdbool.h>
#include "SEGGER_RTT.h"

#include "comm_handlers.h"

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

static Comm_Status_t _handleOperation_GetResult(const Comm_Command_t* command, ByteArray_t response, uint8_t* responseLength)
{
    Comm_Status_t resultStatus;
    if (communicationHandlers[command->header.command].GetResult == NULL)
    {
        SEGGER_RTT_printf(0, "GetResult not implemented for command 0x%X\n", command->header.command);
        resultStatus = Comm_Status_Error_InvalidOperation;
    }
    else
    {
        if (!communicationHandlers[command->header.command].ExecutionInProgress)
        {
            SEGGER_RTT_printf(0, "GetResult called for command 0x%X that is not in progress\n", command->header.command);
            resultStatus = Comm_Status_Error_InvalidOperation;
        }
        else
        {
            resultStatus = communicationHandlers[command->header.command].GetResult(response, responseLength);
            if (resultStatus != Comm_Status_Pending)
            {
                /* Record that the command execution is in progress */
                communicationHandlers[command->header.command].ExecutionInProgress = false;
            }
        }
    }

    return resultStatus;
}

static Comm_Status_t _handleOperation_Start(const Comm_Command_t* command, ByteArray_t response, uint8_t* responseLength)
{
    ConstByteArray_t commandArray = {
        .bytes = command->payload,
        .count = command->header.payloadLength
    };

    Comm_Status_t resultStatus;
    if (communicationHandlers[command->header.command].ExecutionInProgress)
    {
        SEGGER_RTT_printf(0, "Start called for command 0x%X that is already in progress\n", command->header.command);
        resultStatus = Comm_Status_Error_InvalidOperation;
    }
    else
    {
        resultStatus = communicationHandlers[command->header.command].Start(commandArray, response, responseLength);
        if (resultStatus == Comm_Status_Pending)
        {
            /* Record that the command execution is in progress */
            communicationHandlers[command->header.command].ExecutionInProgress = true;

            /* The command is implemented as an async command, but its result may be ready immediately */
            resultStatus = _handleOperation_GetResult(command, response, responseLength);
        }
    }

    return resultStatus;
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
        SEGGER_RTT_printf(
            0,
            "Header CRC error. Command header = [0x%X 0x%X 0x%X]\n",
            command->header.operation,
            command->header.command,
            command->header.payloadLength
        );
        resultStatus = Comm_Status_Error_CommandIntegrityError;
    }
    else if (!_payloadValid(command))
    {
        SEGGER_RTT_printf(
            0,
            "Payload CRC error. Command header = [0x%X 0x%X 0x%X]\n",
            command->header.operation,
            command->header.command,
            command->header.payloadLength
        );
        resultStatus = Comm_Status_Error_PayloadIntegrityError;
    }
    else if (command->header.command >= COMM_HANDLER_COUNT || communicationHandlers[command->header.command].Start == NULL)
    {
        /* unimplemented command */
        SEGGER_RTT_printf(0, "Unknown command 0x%X\n", command->header.command);
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
                // SEGGER_RTT_printf(0, "Start 0x%X: %d\n", command->header.command, resultStatus);
                break;

            case Comm_Operation_GetResult:
                resultStatus = _handleOperation_GetResult(command, responseArray, &payloadSize);
                // SEGGER_RTT_printf(0, "GetResult 0x%X: %d\n", command->header.command, resultStatus);
                break;

            default:
                resultStatus = Comm_Status_Error_UnknownOperation;
                SEGGER_RTT_printf(
                    0,
                    "Unknown operation. Command header = [0x%X 0x%X 0x%X]\n",
                    command->header.operation,
                    command->header.command,
                    command->header.payloadLength
                );
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

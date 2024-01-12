#ifndef COMMUNICATION_MANAGER_H_
#define COMMUNICATION_MANAGER_H_

#include "MasterCommunication.h"
#include <stdio.h>

typedef enum
{
    Comm_Operation_Start,
    Comm_Operation_Restart,
    Comm_Operation_GetResult,
    Comm_Operation_Cancel
} Comm_Operation_t;

typedef struct
{
    Comm_Operation_t operation;
    uint8_t command;
    uint8_t payloadLength;
    uint16_t payloadChecksum;
    uint8_t headerChecksum;
}
__attribute__((packed)) Comm_CommandHeader_t;

typedef struct
{
    Comm_CommandHeader_t header;
    uint8_t payload[];
}
__attribute__((packed)) Comm_Command_t;

typedef struct
{
    Comm_Status_t status;
    uint8_t payloadLength;
    uint16_t payloadChecksum;
    uint8_t headerChecksum;
}
__attribute__((packed)) Comm_ResponseHeader_t;

typedef struct
{
    Comm_ResponseHeader_t header;
    uint8_t payload[];
}
__attribute__((packed)) Comm_Response_t;

/**
 * Initialize the communication handler
 *
 * Sets up command handler to accept and handle commands by calling their respective handlers.
 * Command handlers are defined in the commandTable variable.
 */
void Comm_Init(const Comm_CommandHandler_t* commandTable, size_t commandTableSize);

/**
 * Handle a request and prepare a response
 *
 * @return the response length in bytes
 */
size_t Comm_Handle(const Comm_Command_t* command, Comm_Response_t* response, size_t responseBufferSize);

/**
 * Calculate and set response header checksum
 */
void Comm_ProtectMessageHeader(Comm_ResponseHeader_t* header);

/**
 * Calculate and set response checksum
 */
void Comm_Protect(Comm_Response_t* response);

#endif /* COMMUNICATION_MANAGER_H_ */

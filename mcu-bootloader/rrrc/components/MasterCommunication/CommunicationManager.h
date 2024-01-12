/*
 * CommunicationManager.h
 *
 * This file defines the implemented communication interface above the I2C protocol.
 *
 * Created: 2019. 05. 06. 17:40:11
 *  Author: Dániel Buga
 */ 

#ifndef COMMUNICATION_MANAGER_H_
#define COMMUNICATION_MANAGER_H_

#include <stdio.h>

typedef enum 
{
    Comm_Status_Ok,      /* operation executed successfully, response may contain payload */
    Comm_Status_Busy,    /* command handler is not ready with a response yet */
    Comm_Status_Pending, /* command execution is in progress, no data supplied */
    
    Comm_Status_Error_UnknownOperation,
    Comm_Status_Error_InvalidOperation, /* in case GetResult is used but no command is pending */
    Comm_Status_Error_CommandIntegrityError,
    Comm_Status_Error_PayloadIntegrityError,
    Comm_Status_Error_PayloadLengthError, /* data lost because message was too long */
    Comm_Status_Error_UnknownCommand,
    Comm_Status_Error_CommandError, /* response contains additional command-specific error data */
    Comm_Status_Error_InternalError /* other errors indicating internal programming errors */
} Comm_Status_t;

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
 * Callback type that defines a command handler
 *
 * Command handlers are called by Comm_Handle and run in the communication thread context, in parallel with other application logic
 */
typedef Comm_Status_t (*Comm_CommandHandler_Start_t)(const uint8_t* commandPayload, uint8_t commandSize, uint8_t* response, uint8_t responseBufferSize, uint8_t* responseCount);
typedef Comm_Status_t (*Comm_CommandHandler_GetResult_t)(uint8_t* response, uint8_t responseBufferSize, uint8_t* responseCount);
typedef void (*Comm_CommandHandler_Cancel_t)(void);

typedef struct 
{
    Comm_CommandHandler_Start_t Start;         /* may be NULL in case of an unimplemented command */
    Comm_CommandHandler_GetResult_t GetResult; /* may be NULL when command processing is short */
    Comm_CommandHandler_Cancel_t Cancel;       /* may be NULL */
} Comm_CommandHandler_t;

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

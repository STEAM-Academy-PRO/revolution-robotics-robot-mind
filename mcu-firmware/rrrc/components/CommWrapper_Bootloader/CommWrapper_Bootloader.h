#ifndef COMPONENT_COMM_WRAPPER__BOOTLOADER_H_
#define COMPONENT_COMM_WRAPPER__BOOTLOADER_H_

#ifndef COMPONENT_TYPES_COMM_WRAPPER__BOOTLOADER_H_
#define COMPONENT_TYPES_COMM_WRAPPER__BOOTLOADER_H_

#include <stdint.h>
#include <stdio.h>


typedef enum {
    Comm_Status_Ok,
    Comm_Status_Busy,
    Comm_Status_Pending,
    Comm_Status_Error_UnknownOperation,
    Comm_Status_Error_InvalidOperation,
    Comm_Status_Error_CommandIntegrityError,
    Comm_Status_Error_PayloadIntegrityError,
    Comm_Status_Error_PayloadLengthError,
    Comm_Status_Error_UnknownCommand,
    Comm_Status_Error_CommandError,
    Comm_Status_Error_InternalError
} Comm_Status_t;

typedef struct {
    uint8_t* bytes;
    size_t count;
} ByteArray_t;

typedef struct {
    const uint8_t* bytes;
    size_t count;
} ConstByteArray_t;
typedef Comm_Status_t (*Comm_CommandHandler_Start_t)(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount);
typedef Comm_Status_t (*Comm_CommandHandler_GetResult_t)(ByteArray_t response, uint8_t* responseCount);
typedef void (*Comm_CommandHandler_Cancel_t)(void);

typedef struct {
    Comm_CommandHandler_Start_t Start;
    Comm_CommandHandler_GetResult_t GetResult;
    Comm_CommandHandler_Cancel_t Cancel;
} Comm_CommandHandler_t;

typedef enum {
    AsyncOperationState_Idle,
    AsyncOperationState_Started,
    AsyncOperationState_Busy,
    AsyncOperationState_Done
} AsyncOperationState_t;

#endif /* COMPONENT_TYPES_COMM_WRAPPER__BOOTLOADER_H_ */

/* Begin User Code Section: Declarations */

/* End User Code Section: Declarations */

Comm_Status_t CommWrapper_Bootloader_Run_Command_GetOperationMode_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount);
Comm_Status_t CommWrapper_Bootloader_Run_Command_RebootToBootloader_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount);
AsyncOperationState_t CommWrapper_Bootloader_Async_RebootToBootloader_Call(void);
AsyncOperationState_t CommWrapper_Bootloader_Async_RebootToBootloader_GetResult(void);
void CommWrapper_Bootloader_Async_RebootToBootloader_Cancel(void);

#endif /* COMPONENT_COMM_WRAPPER__BOOTLOADER_H_ */

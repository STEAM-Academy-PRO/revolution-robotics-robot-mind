#ifndef COMPONENT_COMM_WRAPPER__ERROR_STORAGE_H_
#define COMPONENT_COMM_WRAPPER__ERROR_STORAGE_H_

#ifndef COMPONENT_TYPES_COMM_WRAPPER__ERROR_STORAGE_H_
#define COMPONENT_TYPES_COMM_WRAPPER__ERROR_STORAGE_H_

#include "components/ErrorStorage/ErrorStorageTypes.h"
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>


typedef struct {
    const uint8_t* bytes;
    size_t count;
} ConstByteArray_t;

typedef struct {
    uint8_t* bytes;
    size_t count;
} ByteArray_t;

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

#endif /* COMPONENT_TYPES_COMM_WRAPPER__ERROR_STORAGE_H_ */

/* Begin User Code Section: Declarations */

/* End User Code Section: Declarations */

Comm_Status_t CommWrapper_ErrorStorage_Run_Command_ReadCount_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount);
Comm_Status_t CommWrapper_ErrorStorage_Run_Command_ReadErrors_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount);
Comm_Status_t CommWrapper_ErrorStorage_Run_Command_ClearMemory_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount);
Comm_Status_t CommWrapper_ErrorStorage_Run_Command_StoreTestError_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount);
bool CommWrapper_ErrorStorage_Call_Read(uint32_t index, ErrorInfo_t* error);
void CommWrapper_ErrorStorage_Call_Store(const ErrorInfo_t* error);
void CommWrapper_ErrorStorage_Call_ClearMemory(void);
uint32_t CommWrapper_ErrorStorage_Read_NumberOfStoredErrors(void);

#endif /* COMPONENT_COMM_WRAPPER__ERROR_STORAGE_H_ */

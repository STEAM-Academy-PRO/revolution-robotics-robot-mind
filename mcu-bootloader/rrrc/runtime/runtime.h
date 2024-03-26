#ifndef RUNTIME_H_
#define RUNTIME_H_


#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>

#include "rrrc/generated_runtime.h"

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

typedef Comm_Status_t (*Comm_CommandHandler_Start_t)(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount);
typedef Comm_Status_t (*Comm_CommandHandler_GetResult_t)(ByteArray_t response, uint8_t* responseCount);

typedef struct {
    Comm_CommandHandler_Start_t Start;
    Comm_CommandHandler_GetResult_t GetResult;
    bool ExecutionInProgress;
} Comm_CommandHandler_t;

#define COMPONENT_TYPES_MASTER_COMMUNICATION_H_
#define COMPONENT_TYPES_MASTER_COMMUNICATION_INTERFACE_H_
#define COMPONENT_TYPES_VERSION_PROVIDER_H_

#include "components/UpdateManager/UpdateManager.h"
#include "CommonComponents/MasterCommunication/MasterCommunication.h"
#include "components/LEDController_Bootloader/LEDController_Bootloader.h"
#include "components/VersionProvider/VersionProvider.h"
#include "comm_handlers.h"

void Runtime_RequestJumpToApplication(void);

#endif /* RUNTIME_H_ */

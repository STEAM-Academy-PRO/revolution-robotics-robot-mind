#ifndef COMPONENT_MASTER_STATUS_OBSERVER_H_
#define COMPONENT_MASTER_STATUS_OBSERVER_H_

#ifndef COMPONENT_TYPES_MASTER_STATUS_OBSERVER_H_
#define COMPONENT_TYPES_MASTER_STATUS_OBSERVER_H_

#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>


typedef enum {
    MasterStatus_Unknown,
    MasterStatus_NotConfigured,
    MasterStatus_Configuring,
    MasterStatus_Updating,
    MasterStatus_Operational,
    MasterStatus_Controlled
} MasterStatus_t;

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

#endif /* COMPONENT_TYPES_MASTER_STATUS_OBSERVER_H_ */

void MasterStatusObserver_Run_OnInit(void);
void MasterStatusObserver_Run_Update(void);
Comm_Status_t MasterStatusObserver_Run_Command_SetMasterStatus_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount);
void MasterStatusObserver_Write_EnableCommunicationObserver(bool value);
void MasterStatusObserver_Write_MasterStatus(MasterStatus_t value);
uint32_t MasterStatusObserver_Read_ExpectedStartupTime(void);
bool MasterStatusObserver_Read_IsColdStart(void);
uint32_t MasterStatusObserver_Read_UpdateTimeout(void);

#endif /* COMPONENT_MASTER_STATUS_OBSERVER_H_ */

#ifndef COMPONENT_COMM_WRAPPER__MCU_STATUS_COLLECTOR_H_
#define COMPONENT_COMM_WRAPPER__MCU_STATUS_COLLECTOR_H_

#ifndef COMPONENT_TYPES_COMM_WRAPPER__MCU_STATUS_COLLECTOR_H_
#define COMPONENT_TYPES_COMM_WRAPPER__MCU_STATUS_COLLECTOR_H_

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

#endif /* COMPONENT_TYPES_COMM_WRAPPER__MCU_STATUS_COLLECTOR_H_ */

Comm_Status_t CommWrapper_McuStatusCollector_Run_Command_Reset_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount);
Comm_Status_t CommWrapper_McuStatusCollector_Run_Command_ControlSlot_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount);
Comm_Status_t CommWrapper_McuStatusCollector_Run_Command_ReadStatus_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount);
uint8_t CommWrapper_McuStatusCollector_Call_Read(ByteArray_t destination);
void CommWrapper_McuStatusCollector_Call_ResetSlots(void);
void CommWrapper_McuStatusCollector_Call_EnableSlot(uint8_t slot);
void CommWrapper_McuStatusCollector_Call_DisableSlot(uint8_t slot);

#endif /* COMPONENT_COMM_WRAPPER__MCU_STATUS_COLLECTOR_H_ */

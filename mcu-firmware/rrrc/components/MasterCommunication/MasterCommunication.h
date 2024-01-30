#ifndef COMPONENT_MASTER_COMMUNICATION_H_
#define COMPONENT_MASTER_COMMUNICATION_H_

#ifndef COMPONENT_TYPES_MASTER_COMMUNICATION_H_
#define COMPONENT_TYPES_MASTER_COMMUNICATION_H_

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

#endif /* COMPONENT_TYPES_MASTER_COMMUNICATION_H_ */

/* Begin User Code Section: Declarations */

/* End User Code Section: Declarations */

void MasterCommunication_Run_OnInit(const Comm_CommandHandler_t* commandTable, size_t commandTableSize);
void MasterCommunication_Run_HandleCommand(ConstByteArray_t message);
ConstByteArray_t MasterCommunication_Constant_DefaultResponse(void);
ConstByteArray_t MasterCommunication_Constant_LongRxErrorResponse(void);
void MasterCommunication_Call_SendResponse(ConstByteArray_t response);
uint8_t MasterCommunication_Call_Calculate_CRC7(uint8_t init_value, ConstByteArray_t data);
uint16_t MasterCommunication_Call_Calculate_CRC16(uint16_t init_value, ConstByteArray_t data);

#endif /* COMPONENT_MASTER_COMMUNICATION_H_ */

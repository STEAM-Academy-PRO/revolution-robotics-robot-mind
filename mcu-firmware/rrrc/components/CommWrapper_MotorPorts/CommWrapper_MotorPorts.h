#ifndef COMPONENT_COMM_WRAPPER__MOTOR_PORTS_H_
#define COMPONENT_COMM_WRAPPER__MOTOR_PORTS_H_

#ifndef COMPONENT_TYPES_COMM_WRAPPER__MOTOR_PORTS_H_
#define COMPONENT_TYPES_COMM_WRAPPER__MOTOR_PORTS_H_

#include "Config/atmel_start_pins.h"
#include <float.h>
#include <stdbool.h>
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
    bool ExecutionInProgress;
} Comm_CommandHandler_t;

typedef struct {
    gpio_pin_t led;
    fast_gpio_t enc0;
    fast_gpio_t enc1;
} MotorPortGpios_t;

typedef struct {
    uint8_t port_idx;
    const void* library;
    void* libraryData;
    MotorPortGpios_t gpio;
} MotorPort_t;

typedef enum {
    DriveRequest_RequestType_Speed,
    DriveRequest_RequestType_Position,
    DriveRequest_RequestType_Power
} DriveRequest_RequestType_t;

typedef union {
    float speed;
    int32_t position;
    int16_t power;
} DriveRequest_RequestValue_t;

typedef struct {
    uint8_t version;
    float power_limit;
    float speed_limit;
    DriveRequest_RequestType_t request_type;
    DriveRequest_RequestValue_t request;
    float positionBreakpoint;
} DriveRequest_t;
typedef float Current_t;
typedef float Percentage_t;

typedef enum {
    AsyncOperationState_Idle,
    AsyncOperationState_Started,
    AsyncOperationState_Busy,
    AsyncOperationState_Done
} AsyncOperationState_t;

#endif /* COMPONENT_TYPES_COMM_WRAPPER__MOTOR_PORTS_H_ */

/* Begin User Code Section: Declarations */

/* End User Code Section: Declarations */

Comm_Status_t CommWrapper_MotorPorts_Run_Command_GetPortAmount_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount);
Comm_Status_t CommWrapper_MotorPorts_Run_Command_GetPortTypes_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount);
Comm_Status_t CommWrapper_MotorPorts_Run_Command_SetPortType_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount);
Comm_Status_t CommWrapper_MotorPorts_Run_Command_SetPortType_GetResult(ByteArray_t response, uint8_t* responseCount);
Comm_Status_t CommWrapper_MotorPorts_Run_Command_SetPortConfig_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount);
Comm_Status_t CommWrapper_MotorPorts_Run_Command_SetPortConfig_GetResult(ByteArray_t response, uint8_t* responseCount);
Comm_Status_t CommWrapper_MotorPorts_Run_Command_SetControlValue_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount);
Comm_Status_t CommWrapper_MotorPorts_Run_Command_TestMotorOnPort_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount);
Comm_Status_t CommWrapper_MotorPorts_Run_Command_TestMotorOnPort_GetResult(ByteArray_t response, uint8_t* responseCount);
AsyncOperationState_t CommWrapper_MotorPorts_Async_SetPortType_Call(uint8_t port_idx, uint8_t port_type);
AsyncOperationState_t CommWrapper_MotorPorts_Async_SetPortType_GetResult(bool* result);
void CommWrapper_MotorPorts_Async_SetPortType_Cancel(void);
AsyncOperationState_t CommWrapper_MotorPorts_Async_SetPortConfig_Call(uint8_t port_idx, ByteArray_t configuration);
AsyncOperationState_t CommWrapper_MotorPorts_Async_SetPortConfig_GetResult(bool* result);
void CommWrapper_MotorPorts_Async_SetPortConfig_Cancel(void);
AsyncOperationState_t CommWrapper_MotorPorts_Async_TestMotorOnPort_Call(uint8_t port_idx, uint8_t test_power, uint8_t threshold);
AsyncOperationState_t CommWrapper_MotorPorts_Async_TestMotorOnPort_GetResult(bool* result);
void CommWrapper_MotorPorts_Async_TestMotorOnPort_Cancel(void);
void CommWrapper_MotorPorts_Call_ReadPortTypes(ByteArray_t* buffer);
bool CommWrapper_MotorPorts_Call_CreateDriveRequest(uint8_t port_idx, ConstByteArray_t buffer, DriveRequest_t* request);
void CommWrapper_MotorPorts_Write_DriveRequest(uint32_t index, const DriveRequest_t* value);
uint8_t CommWrapper_MotorPorts_Read_PortCount(void);

#endif /* COMPONENT_COMM_WRAPPER__MOTOR_PORTS_H_ */

#ifndef COMPONENT_COMM_WRAPPER__SENSOR_PORTS_H_
#define COMPONENT_COMM_WRAPPER__SENSOR_PORTS_H_

#ifndef COMPONENT_TYPES_COMM_WRAPPER__SENSOR_PORTS_H_
#define COMPONENT_TYPES_COMM_WRAPPER__SENSOR_PORTS_H_

#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>


typedef enum {
    TestSensorOnPortResult_NotPresent,
    TestSensorOnPortResult_Present,
    TestSensorOnPortResult_Unknown,
    TestSensorOnPortResult_Error
} TestSensorOnPortResult_t;

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

typedef enum {
    AsyncOperationState_Idle,
    AsyncOperationState_Started,
    AsyncOperationState_Busy,
    AsyncOperationState_Done
} AsyncOperationState_t;

#endif /* COMPONENT_TYPES_COMM_WRAPPER__SENSOR_PORTS_H_ */

/* Begin User Code Section: Declarations */

/* End User Code Section: Declarations */

Comm_Status_t CommWrapper_SensorPorts_Run_Command_GetPortAmount_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount);
Comm_Status_t CommWrapper_SensorPorts_Run_Command_GetPortTypes_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount);
Comm_Status_t CommWrapper_SensorPorts_Run_Command_SetPortType_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount);
Comm_Status_t CommWrapper_SensorPorts_Run_Command_SetPortType_GetResult(ByteArray_t response, uint8_t* responseCount);
Comm_Status_t CommWrapper_SensorPorts_Run_Command_SetPortConfig_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount);
Comm_Status_t CommWrapper_SensorPorts_Run_Command_SetPortConfig_GetResult(ByteArray_t response, uint8_t* responseCount);
Comm_Status_t CommWrapper_SensorPorts_Run_Command_ReadSensorInfo_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount);
Comm_Status_t CommWrapper_SensorPorts_Run_Command_TestSensorOnPort_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount);
Comm_Status_t CommWrapper_SensorPorts_Run_Command_TestSensorOnPort_GetResult(ByteArray_t response, uint8_t* responseCount);
AsyncOperationState_t CommWrapper_SensorPorts_Async_TestSensorOnPort_Call(uint8_t port_idx, uint8_t port_type);
AsyncOperationState_t CommWrapper_SensorPorts_Async_TestSensorOnPort_GetResult(TestSensorOnPortResult_t* result);
void CommWrapper_SensorPorts_Async_TestSensorOnPort_Cancel(void);
AsyncOperationState_t CommWrapper_SensorPorts_Async_SetPortType_Call(uint8_t port_idx, uint8_t port_type);
AsyncOperationState_t CommWrapper_SensorPorts_Async_SetPortType_GetResult(bool* result);
void CommWrapper_SensorPorts_Async_SetPortType_Cancel(void);
AsyncOperationState_t CommWrapper_SensorPorts_Async_SetPortConfig_Call(uint8_t port_idx, ByteArray_t configuration);
AsyncOperationState_t CommWrapper_SensorPorts_Async_SetPortConfig_GetResult(bool* result);
void CommWrapper_SensorPorts_Async_SetPortConfig_Cancel(void);
void CommWrapper_SensorPorts_Call_ReadPortTypes(ByteArray_t* buffer);
void CommWrapper_SensorPorts_Call_ReadSensorInfo(uint8_t port_idx, uint8_t page, ByteArray_t* buffer);
uint8_t CommWrapper_SensorPorts_Read_PortCount(void);

#endif /* COMPONENT_COMM_WRAPPER__SENSOR_PORTS_H_ */

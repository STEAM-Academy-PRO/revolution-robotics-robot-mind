#ifndef COMPONENT_SENSOR_PORT_HANDLER_H_
#define COMPONENT_SENSOR_PORT_HANDLER_H_

#ifndef COMPONENT_TYPES_SENSOR_PORT_HANDLER_H_
#define COMPONENT_TYPES_SENSOR_PORT_HANDLER_H_

#include <float.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>


typedef struct {
    uint8_t* bytes;
    size_t count;
} ByteArray_t;

typedef enum {
    AsyncCommand_None,
    AsyncCommand_Start,
    AsyncCommand_Continue,
    AsyncCommand_Cancel
} AsyncCommand_t;

typedef enum {
    AsyncResult_Pending,
    AsyncResult_Ok
} AsyncResult_t;

typedef enum {
    TestSensorOnPortResult_NotPresent,
    TestSensorOnPortResult_Present,
    TestSensorOnPortResult_Unknown,
    TestSensorOnPortResult_Error
} TestSensorOnPortResult_t;

#endif /* COMPONENT_TYPES_SENSOR_PORT_HANDLER_H_ */

/* Begin User Code Section: Declarations */
struct _SensorPort_t;

#include "SensorPortLibraries/SensorPort_I2C.h"
#include "SensorPortLibraries/SensorPort_UART.h"
#include "SensorPortLibraries/SensorPortLibrary.h"

typedef enum {
    SensorPortComm_None,
    SensorPortComm_I2C,
    SensorPortComm_UART
} SensorPort_CommInterface_t;

typedef enum {
    SetPortTypeState_None,
    SetPortTypeState_Busy,
    SetPortTypeState_Done,
} SetPortTypeState_t;

typedef struct _SensorPort_t
{
    uint8_t port_idx;

    /* Driver implementation VTable */
    const struct _SensorLibrary_t* library;
    /* Driver implementation private data */
    void* libraryData;

    uint8_t led0;
    uint8_t led1;

    uint8_t gpio0;
    uint8_t gpio1;
    uint8_t vccio;

    struct {
        uint8_t pin;
        uint8_t function;
    } comm_pin0, comm_pin1;

    void* comm_hw;
    SetPortTypeState_t set_port_type_state;

    SensorPort_CommInterface_t interfaceType;
    union {
        UARTInstance_t uart;
        SensorPort_I2CMaster_Instance_t i2cm;
    } sercom;
} SensorPort_t;

/* TODO generate this as well */
void SensorPortHandler_Run_OnInit(SensorPort_t* ports, size_t portCount);
/* End User Code Section: Declarations */

void SensorPortHandler_Run_PortUpdate(uint8_t port_idx);
void SensorPortHandler_Run_ReadPortTypes(ByteArray_t* buffer);
void SensorPortHandler_Run_Configure(uint8_t port_idx, ByteArray_t configuration, bool* result);
void SensorPortHandler_Run_ReadSensorInfo(uint8_t port_idx, uint8_t page, ByteArray_t* buffer);
AsyncResult_t SensorPortHandler_AsyncRunnable_SetPortType(AsyncCommand_t asyncCommand, uint8_t port_idx, uint8_t port_type, bool* result);
AsyncResult_t SensorPortHandler_AsyncRunnable_TestSensorOnPort(AsyncCommand_t asyncCommand, uint8_t port_idx, uint8_t port_type, TestSensorOnPortResult_t* result);
uint8_t SensorPortHandler_Constant_PortCount(void);
void* SensorPortHandler_Call_Allocate(size_t size);
void SensorPortHandler_Call_Free(void** ptr);
uint32_t SensorPortHandler_Call_ReadCurrentTicks(void);
float SensorPortHandler_Call_ConvertTicksToMs(uint32_t ticks);
void SensorPortHandler_Call_UpdatePortStatus(uint8_t port, ByteArray_t data);
uint8_t SensorPortHandler_Read_AdcData(uint32_t index);

#endif /* COMPONENT_SENSOR_PORT_HANDLER_H_ */

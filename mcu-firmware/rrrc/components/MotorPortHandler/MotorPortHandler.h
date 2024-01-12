#ifndef COMPONENT_MOTOR_PORT_HANDLER_H_
#define COMPONENT_MOTOR_PORT_HANDLER_H_

#ifndef COMPONENT_TYPES_MOTOR_PORT_HANDLER_H_
#define COMPONENT_TYPES_MOTOR_PORT_HANDLER_H_

#include "Config/atmel_start_pins.h"
#include <float.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>


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
    uint32_t version;
    float power_limit;
    float speed_limit;
    DriveRequest_RequestType_t request_type;
    DriveRequest_RequestValue_t request;
} DriveRequest_t;
typedef float Current_t;
typedef float Percentage_t;

typedef struct {
    uint8_t* bytes;
    size_t count;
} ByteArray_t;

typedef struct {
    const uint8_t* bytes;
    size_t count;
} ConstByteArray_t;

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

#endif /* COMPONENT_TYPES_MOTOR_PORT_HANDLER_H_ */

/* TODO generate OnInit */
void MotorPortHandler_Run_OnInit(MotorPort_t* ports, uint8_t portCount);
void MotorPortHandler_Run_PortUpdate(uint8_t port_idx);
void MotorPortHandler_Run_ReadPortTypes(ByteArray_t* buffer);
void MotorPortHandler_Run_SetPortType(uint8_t port_idx, uint8_t port_type, bool* result);
void MotorPortHandler_Run_Configure(uint8_t port_idx, ByteArray_t configuration, bool* result);
bool MotorPortHandler_Run_CreateDriveRequest(uint8_t port_idx, ConstByteArray_t buffer, DriveRequest_t* request);
AsyncResult_t MotorPortHandler_AsyncRunnable_TestMotorOnPort(AsyncCommand_t asyncCommand, uint8_t port_idx, uint8_t test_power, uint8_t threshold, bool* result);
void* MotorPortHandler_Call_Allocate(size_t size);
void MotorPortHandler_Call_Free(void** ptr);
void MotorPortHandler_Call_UpdatePortStatus(uint8_t port, ByteArray_t data);
void MotorPortHandler_Write_DriveStrength(uint32_t index, int16_t value);
void MotorPortHandler_Write_MaxAllowedCurrent(uint32_t index, Current_t value);
void MotorPortHandler_Write_PortCount(uint8_t value);
void MotorPortHandler_Read_DriveRequest(uint32_t index, DriveRequest_t* value);
void MotorPortHandler_Read_PortConfig(uint32_t index, MotorPortGpios_t* value);
Percentage_t MotorPortHandler_Read_RelativeMotorCurrent(uint32_t index);

#endif /* COMPONENT_MOTOR_PORT_HANDLER_H_ */

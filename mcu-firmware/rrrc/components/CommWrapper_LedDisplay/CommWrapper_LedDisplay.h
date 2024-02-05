#ifndef COMPONENT_COMM_WRAPPER__LED_DISPLAY_H_
#define COMPONENT_COMM_WRAPPER__LED_DISPLAY_H_

#ifndef COMPONENT_TYPES_COMM_WRAPPER__LED_DISPLAY_H_
#define COMPONENT_TYPES_COMM_WRAPPER__LED_DISPLAY_H_

#include "utils/color.h"
#include <stdint.h>
#include <stdio.h>


typedef enum {
    RingLedScenario_Off,
    RingLedScenario_UserFrame,
    RingLedScenario_ColorWheel,
    RingLedScenario_RainbowFade,
    RingLedScenario_BusyIndicator,
    RingLedScenario_BreathingGreen,
    RingLedScenario_Siren,
    RingLedScenario_TrafficLight
} RingLedScenario_t;

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

#endif /* COMPONENT_TYPES_COMM_WRAPPER__LED_DISPLAY_H_ */

/* Begin User Code Section: Declarations */

/* End User Code Section: Declarations */

void CommWrapper_LedDisplay_Run_Reset(void);
Comm_Status_t CommWrapper_LedDisplay_Run_Command_GetScenarioTypes_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount);
Comm_Status_t CommWrapper_LedDisplay_Run_Command_SetScenarioType_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount);
Comm_Status_t CommWrapper_LedDisplay_Run_Command_GetRingLedAmount_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount);
Comm_Status_t CommWrapper_LedDisplay_Run_Command_SetUserFrame_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount);
ssize_t CommWrapper_LedDisplay_Call_ReadScenarioName(RingLedScenario_t scenario, ByteArray_t destination);
void CommWrapper_LedDisplay_Write_Scenario(RingLedScenario_t value);
void CommWrapper_LedDisplay_Write_UserFrame(uint32_t index, rgb_t value);
size_t CommWrapper_LedDisplay_Read_ScenarioCount(void);

#endif /* COMPONENT_COMM_WRAPPER__LED_DISPLAY_H_ */

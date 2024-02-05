#ifndef COMPONENT_RING_LED_DISPLAY_H_
#define COMPONENT_RING_LED_DISPLAY_H_

#ifndef COMPONENT_TYPES_RING_LED_DISPLAY_H_
#define COMPONENT_TYPES_RING_LED_DISPLAY_H_

#include "utils/color.h"
#include <stdbool.h>
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
    RingLedScenario_TrafficLight,
    RingLedScenario_BugIndicator
} RingLedScenario_t;

typedef enum {
    MasterStatus_Unknown,
    MasterStatus_NotConfigured,
    MasterStatus_Configuring,
    MasterStatus_Updating,
    MasterStatus_Operational,
    MasterStatus_Controlled
} MasterStatus_t;

typedef struct {
    uint8_t* bytes;
    size_t count;
} ByteArray_t;

#endif /* COMPONENT_TYPES_RING_LED_DISPLAY_H_ */

/* Begin User Code Section: Declarations */

/* End User Code Section: Declarations */

void RingLedDisplay_Run_OnInit(void);
void RingLedDisplay_Run_Update(void);
void RingLedDisplay_Run_OnMasterStarted(void);
ssize_t RingLedDisplay_Run_ReadScenarioName(RingLedScenario_t scenario, ByteArray_t destination);
size_t RingLedDisplay_Constant_ScenarioCount(void);
void RingLedDisplay_Write_LedColor(uint32_t index, rgb_t value);
uint32_t RingLedDisplay_Read_ExpectedStartupTime(void);
MasterStatus_t RingLedDisplay_Read_MasterStatus(void);
RingLedScenario_t RingLedDisplay_Read_Scenario(void);
rgb_t RingLedDisplay_Read_UserColors(uint32_t index);
bool RingLedDisplay_Read_WaitForMasterStartup(void);

#endif /* COMPONENT_RING_LED_DISPLAY_H_ */

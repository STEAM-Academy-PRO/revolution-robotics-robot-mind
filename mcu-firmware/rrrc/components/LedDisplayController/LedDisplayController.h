#ifndef COMPONENT_LED_DISPLAY_CONTROLLER_H_
#define COMPONENT_LED_DISPLAY_CONTROLLER_H_

#ifndef COMPONENT_TYPES_LED_DISPLAY_CONTROLLER_H_
#define COMPONENT_TYPES_LED_DISPLAY_CONTROLLER_H_

#include "CommonLibraries/color.h"
#include <stdbool.h>
#include <stdint.h>


typedef enum {
    ChargerState_NotPluggedIn,
    ChargerState_Charging,
    ChargerState_Charged,
    ChargerState_Fault
} ChargerState_t;

typedef enum {
    MasterStatus_Unknown,
    MasterStatus_NotConfigured,
    MasterStatus_Configuring,
    MasterStatus_Updating,
    MasterStatus_Operational,
    MasterStatus_Controlled
} MasterStatus_t;

typedef enum {
    BluetoothStatus_Inactive,
    BluetoothStatus_NotConnected,
    BluetoothStatus_Connected
} BluetoothStatus_t;

#endif /* COMPONENT_TYPES_LED_DISPLAY_CONTROLLER_H_ */

/* Begin User Code Section: Declarations */

/* End User Code Section: Declarations */

void LedDisplayController_Run_OnInit(void);
void LedDisplayController_Run_Update(void);
void LedDisplayController_Write_MaxBrightness(uint8_t value);
void LedDisplayController_Write_RingLeds(uint32_t index, rgb_t value);
void LedDisplayController_Write_StatusLeds(uint32_t index, rgb_t value);
BluetoothStatus_t LedDisplayController_Read_BluetoothStatus(void);
uint8_t LedDisplayController_Read_DefaultBrightness(void);
uint8_t LedDisplayController_Read_LowBatteryBrightness(void);
bool LedDisplayController_Read_MainBatteryDetected(void);
uint8_t LedDisplayController_Read_MainBatteryLevel(void);
bool LedDisplayController_Read_MainBatteryLow(void);
ChargerState_t LedDisplayController_Read_MainBatteryStatus(void);
MasterStatus_t LedDisplayController_Read_MasterStatus(void);
uint8_t LedDisplayController_Read_MotorBatteryLevel(void);
bool LedDisplayController_Read_MotorBatteryPresent(void);
int16_t LedDisplayController_Read_MotorDriveValues(uint32_t index);
uint8_t LedDisplayController_Read_PowerOffBrightness(void);
rgb_t LedDisplayController_Read_RingLedsIn(uint32_t index);

#endif /* COMPONENT_LED_DISPLAY_CONTROLLER_H_ */

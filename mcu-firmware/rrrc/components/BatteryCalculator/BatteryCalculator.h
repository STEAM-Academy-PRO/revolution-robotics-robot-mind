#ifndef COMPONENT_BATTERY_CALCULATOR_H_
#define COMPONENT_BATTERY_CALCULATOR_H_

#ifndef COMPONENT_TYPES_BATTERY_CALCULATOR_H_
#define COMPONENT_TYPES_BATTERY_CALCULATOR_H_

#include <float.h>
#include <stdbool.h>
#include <stdint.h>

typedef float Voltage_t;

typedef struct {
    Voltage_t detectionVoltage;
    Voltage_t minVoltage;
    Voltage_t maxVoltage;
} BatteryConfiguration_t;

#endif /* COMPONENT_TYPES_BATTERY_CALCULATOR_H_ */

/* Begin User Code Section: Declarations */

/* End User Code Section: Declarations */

void BatteryCalculator_Run_OnInit(void);
void BatteryCalculator_Run_Update(void);
void BatteryCalculator_Write_MainBatteryLevel(uint8_t value);
void BatteryCalculator_Write_MainBatteryLow(bool value);
void BatteryCalculator_Write_MotorBatteryLevel(uint8_t value);
void BatteryCalculator_Write_MotorBatteryPresent(bool value);
void BatteryCalculator_Read_MainBatteryParameters(BatteryConfiguration_t* value);
Voltage_t BatteryCalculator_Read_MainBatteryVoltage(void);
void BatteryCalculator_Read_MotorBatteryParameters(BatteryConfiguration_t* value);
Voltage_t BatteryCalculator_Read_MotorBatteryVoltage(void);

#endif /* COMPONENT_BATTERY_CALCULATOR_H_ */

#ifndef COMPONENT_PROJECT_CONFIGURATION_H_
#define COMPONENT_PROJECT_CONFIGURATION_H_

#ifndef COMPONENT_TYPES_PROJECT_CONFIGURATION_H_
#define COMPONENT_TYPES_PROJECT_CONFIGURATION_H_

#include "Config/atmel_start_pins.h"
#include <float.h>
#include <stdint.h>
#include <stdio.h>

typedef float Voltage_t;
typedef float Temperature_t;

typedef struct {
    Voltage_t detectionVoltage;
    Voltage_t minVoltage;
    Voltage_t maxVoltage;
} BatteryConfiguration_t;

typedef struct {
    float resistance;
    float coeff_cooling;
    float coeff_heating;
} MotorThermalParameters_t;

typedef struct {
    Temperature_t MaxSafeTemperature;
    Temperature_t MaxAllowedTemperature;
} MotorDeratingParameters_t;

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
    uint32_t positionBreakpoint;
} DriveRequest_t;
typedef float Current_t;
typedef float Percentage_t;

#endif /* COMPONENT_TYPES_PROJECT_CONFIGURATION_H_ */

/* Begin User Code Section: Declarations */

/* End User Code Section: Declarations */

uint8_t ProjectConfiguration_Constant_DeviceAddress(void);
uint32_t ProjectConfiguration_Constant_ExpectedStartupTime(void);
uint32_t ProjectConfiguration_Constant_ExpectedUpdateTime(void);
void ProjectConfiguration_Constant_MainBatteryParameters(BatteryConfiguration_t* value);
void ProjectConfiguration_Constant_MotorBatteryParameters(BatteryConfiguration_t* value);
void ProjectConfiguration_Constant_MotorDeratingParameters(MotorDeratingParameters_t* value);
void ProjectConfiguration_Constant_MotorPortGpios(uint32_t index, MotorPortGpios_t* value);
void ProjectConfiguration_Constant_MotorThermalParameters(MotorThermalParameters_t* value);

#endif /* COMPONENT_PROJECT_CONFIGURATION_H_ */

#ifndef GENERATED_RUNTIME_H_
#define GENERATED_RUNTIME_H_

#include "Config/atmel_start_pins.h"
#include "components/ErrorStorage/ErrorStorageTypes.h"
#include "libraries/color.h"
#include <float.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>


typedef enum {
    AsyncOperationState_Idle,
    AsyncOperationState_Started,
    AsyncOperationState_Busy,
    AsyncOperationState_Done
} AsyncOperationState_t;

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
typedef float Voltage_t;
typedef float Current_t;

typedef struct {
    Voltage_t detectionVoltage;
    Voltage_t minVoltage;
    Voltage_t maxVoltage;
} BatteryConfiguration_t;

typedef enum {
    ChargerState_NotPluggedIn,
    ChargerState_Charging,
    ChargerState_Charged,
    ChargerState_Fault
} ChargerState_t;

typedef enum {
    BluetoothStatus_Inactive,
    BluetoothStatus_NotConnected,
    BluetoothStatus_Connected
} BluetoothStatus_t;

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

typedef struct {
    Comm_CommandHandler_Start_t Start;
    Comm_CommandHandler_GetResult_t GetResult;
    bool ExecutionInProgress;
} Comm_CommandHandler_t;

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
typedef float Percentage_t;

typedef enum {
    TestSensorOnPortResult_NotPresent,
    TestSensorOnPortResult_Present,
    TestSensorOnPortResult_Unknown,
    TestSensorOnPortResult_Error
} TestSensorOnPortResult_t;

typedef struct {
    float x;
    float y;
    float z;
} Vector3D_t;

typedef struct {
    int16_t x;
    int16_t y;
    int16_t z;
} IMU_RawSample_t;

typedef struct {
    float pitch;
    float roll;
    float yaw;
} Orientation3D_t;

typedef struct {
    float q0;
    float q1;
    float q2;
    float q3;
} Quaternion_t;

typedef struct {
    ConstByteArray_t default_response;
    ConstByteArray_t rx_overflow_response;
    uint32_t rx_timeout;
} MasterCommunicationInterface_Config_t;

typedef struct {
    ByteArray_t data;
    uint8_t version;
} SlotData_t;
typedef float Temperature_t;

typedef struct {
    Temperature_t MaxSafeTemperature;
    Temperature_t MaxAllowedTemperature;
} MotorDeratingParameters_t;

typedef struct {
    float resistance;
    float coeff_cooling;
    float coeff_heating;
} MotorThermalParameters_t;

typedef enum {
    QueueStatus_Empty,
    QueueStatus_Ok,
    QueueStatus_Overflow
} QueueStatus_t;

#define COMPONENT_TYPES_ADC_H_
#define COMPONENT_TYPES_BATTERY_CALCULATOR_H_
#define COMPONENT_TYPES_BATTERY_CHARGER_H_
#define COMPONENT_TYPES_BLUETOOTH_STATUS_OBSERVER_H_
#define COMPONENT_TYPES_MASTER_COMMUNICATION_H_
#define COMPONENT_TYPES_CRC_H_
#define COMPONENT_TYPES_COMM_WRAPPER__BOOTLOADER_H_
#define COMPONENT_TYPES_COMM_WRAPPER__ERROR_STORAGE_H_
#define COMPONENT_TYPES_ERROR_STORAGE_H_
#define COMPONENT_TYPES_COMM_WRAPPER__LED_DISPLAY_H_
#define COMPONENT_TYPES_RING_LED_DISPLAY_H_
#define COMPONENT_TYPES_COMM_WRAPPER__MCU_STATUS_COLLECTOR_H_
#define COMPONENT_TYPES_COMM_WRAPPER__MOTOR_PORTS_H_
#define COMPONENT_TYPES_MOTOR_PORT_HANDLER_H_
#define COMPONENT_TYPES_COMM_WRAPPER__SENSOR_PORTS_H_
#define COMPONENT_TYPES_COMM_WRAPPER__VERSION_PROVIDER_H_
#define COMPONENT_TYPES_VERSION_PROVIDER_H_
#define COMPONENT_TYPES_COMMUNICATION_OBSERVER_H_
#define COMPONENT_TYPES_CONFIG_EVENT_PROVIDER_H_
#define COMPONENT_TYPES_GYROSCOPE_OFFSET_COMPENSATOR_H_
#define COMPONENT_TYPES_HARDWARE_COMPATIBILITY_CHECKER_H_
#define COMPONENT_TYPES_HIGH_RESOLUTION_TIMER_H_
#define COMPONENT_TYPES_IMU_H_
#define COMPONENT_TYPES_IMU_MOVEMENT_DETECTOR_H_
#define COMPONENT_TYPES_IMU_ORIENTATION_ESTIMATOR_H_
#define COMPONENT_TYPES_INTERNAL_TEMPERATURE_SENSOR_H_
#define COMPONENT_TYPES_LED_CONTROLLER_H_
#define COMPONENT_TYPES_LED_DISPLAY_CONTROLLER_H_
#define COMPONENT_TYPES_MASTER_STATUS_OBSERVER_H_
#define COMPONENT_TYPES_MASTER_COMMUNICATION_INTERFACE_H_
#define COMPONENT_TYPES_MCU_STATUS_COLLECTOR_H_
#define COMPONENT_TYPES_MCU_STATUS_SLOTS_H_
#define COMPONENT_TYPES_MEMORY_ALLOCATOR_H_
#define COMPONENT_TYPES_MOTOR_CURRENT_FILTER_H_
#define COMPONENT_TYPES_MOTOR_DERATING_H_
#define COMPONENT_TYPES_MOTOR_DRIVER_8833_H_
#define COMPONENT_TYPES_MOTOR_THERMAL_MODEL_H_
#define COMPONENT_TYPES_PROJECT_CONFIGURATION_H_
#define COMPONENT_TYPES_RESTART_MANAGER_H_
#define COMPONENT_TYPES_SENSOR_PORT_HANDLER_H_
#define COMPONENT_TYPES_STARTUP_REASON_PROVIDER_H_
#define COMPONENT_TYPES_WATCHDOG_FEEDER_H_

#include "rrrc/components/ADC/ADC.h"
#include "rrrc/components/BatteryCalculator/BatteryCalculator.h"
#include "rrrc/components/BatteryCharger/BatteryCharger.h"
#include "rrrc/components/BluetoothStatusObserver/BluetoothStatusObserver.h"
#include "../mcu-common/CommonComponents/MasterCommunication/MasterCommunication.h"
#include "rrrc/components/CRC/CRC.h"
#include "rrrc/components/CommWrapper_Bootloader/CommWrapper_Bootloader.h"
#include "rrrc/components/CommWrapper_ErrorStorage/CommWrapper_ErrorStorage.h"
#include "rrrc/components/ErrorStorage/ErrorStorage.h"
#include "rrrc/components/CommWrapper_LedDisplay/CommWrapper_LedDisplay.h"
#include "rrrc/components/RingLedDisplay/RingLedDisplay.h"
#include "rrrc/components/CommWrapper_McuStatusCollector/CommWrapper_McuStatusCollector.h"
#include "rrrc/components/CommWrapper_MotorPorts/CommWrapper_MotorPorts.h"
#include "rrrc/components/MotorPortHandler/MotorPortHandler.h"
#include "rrrc/components/CommWrapper_SensorPorts/CommWrapper_SensorPorts.h"
#include "rrrc/components/CommWrapper_VersionProvider/CommWrapper_VersionProvider.h"
#include "rrrc/components/VersionProvider/VersionProvider.h"
#include "rrrc/components/CommunicationObserver/CommunicationObserver.h"
#include "rrrc/components/ConfigEventProvider/ConfigEventProvider.h"
#include "rrrc/components/GyroscopeOffsetCompensator/GyroscopeOffsetCompensator.h"
#include "rrrc/components/HardwareCompatibilityChecker/HardwareCompatibilityChecker.h"
#include "rrrc/components/HighResolutionTimer/HighResolutionTimer.h"
#include "rrrc/components/IMU/IMU.h"
#include "rrrc/components/IMUMovementDetector/IMUMovementDetector.h"
#include "rrrc/components/IMUOrientationEstimator/IMUOrientationEstimator.h"
#include "rrrc/components/InternalTemperatureSensor/InternalTemperatureSensor.h"
#include "rrrc/components/LEDController/LEDController.h"
#include "rrrc/components/LedDisplayController/LedDisplayController.h"
#include "rrrc/components/MasterStatusObserver/MasterStatusObserver.h"
#include "rrrc/components/MasterCommunicationInterface/MasterCommunicationInterface.h"
#include "rrrc/components/McuStatusCollector/McuStatusCollector.h"
#include "rrrc/components/McuStatusSlots/McuStatusSlots.h"
#include "rrrc/components/MemoryAllocator/MemoryAllocator.h"
#include "rrrc/components/MotorCurrentFilter/MotorCurrentFilter.h"
#include "rrrc/components/MotorDerating/MotorDerating.h"
#include "rrrc/components/MotorDriver_8833/MotorDriver_8833.h"
#include "rrrc/components/MotorThermalModel/MotorThermalModel.h"
#include "rrrc/components/ProjectConfiguration/ProjectConfiguration.h"
#include "rrrc/components/RestartManager/RestartManager.h"
#include "rrrc/components/SensorPortHandler/SensorPortHandler.h"
#include "rrrc/components/StartupReasonProvider/StartupReasonProvider.h"
#include "rrrc/components/WatchdogFeeder/WatchdogFeeder.h"

void Runtime_RaiseEvent_OnInit(void);
void Runtime_RaiseEvent_OnInitDone(void);
void Runtime_RaiseEvent_1ms(void);
void Runtime_RaiseEvent_10ms_offset0(void);
void Runtime_RaiseEvent_10ms_offset1(void);
void Runtime_RaiseEvent_10ms_offset2(void);
void Runtime_RaiseEvent_10ms_offset3(void);
void Runtime_RaiseEvent_10ms_offset4(void);
void Runtime_RaiseEvent_10ms_offset5(void);
void Runtime_RaiseEvent_10ms_offset6(void);
void Runtime_RaiseEvent_10ms_offset7(void);
void Runtime_RaiseEvent_10ms_offset8(void);
void Runtime_RaiseEvent_10ms_offset9(void);
void Runtime_RaiseEvent_20ms_offset0(void);
void Runtime_RaiseEvent_20ms_offset1(void);
void Runtime_RaiseEvent_20ms_offset2(void);
void Runtime_RaiseEvent_20ms_offset3(void);
void Runtime_RaiseEvent_20ms_offset4(void);
void Runtime_RaiseEvent_20ms_offset5(void);
void Runtime_RaiseEvent_20ms_offset6(void);
void Runtime_RaiseEvent_20ms_offset7(void);
void Runtime_RaiseEvent_20ms_offset8(void);
void Runtime_RaiseEvent_20ms_offset9(void);
void Runtime_RaiseEvent_20ms_offset10(void);
void Runtime_RaiseEvent_20ms_offset11(void);
void Runtime_RaiseEvent_20ms_offset12(void);
void Runtime_RaiseEvent_20ms_offset13(void);
void Runtime_RaiseEvent_20ms_offset14(void);
void Runtime_RaiseEvent_20ms_offset15(void);
void Runtime_RaiseEvent_20ms_offset16(void);
void Runtime_RaiseEvent_20ms_offset17(void);
void Runtime_RaiseEvent_20ms_offset18(void);
void Runtime_RaiseEvent_20ms_offset19(void);
void Runtime_RaiseEvent_100ms(void);

#endif /* GENERATED_RUNTIME_H */

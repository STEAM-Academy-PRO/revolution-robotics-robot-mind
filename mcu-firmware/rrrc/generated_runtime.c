#include "generated_runtime.h"
#include "utils.h"
#include "utils_assert.h"

/* Begin User Code Section: Declarations */

/* End User Code Section: Declarations */
static uint32_t ErrorStorage_NumberOfStoredErrors_variable = 0u;
static bool MasterStatusObserver_EnableCommunicationObserver_variable = false;
static Vector3D_t IMU_GyroscopeSample_queue[8u];
static size_t IMU_GyroscopeSample_queue_count = 0u;
static size_t IMU_GyroscopeSample_queue_write_index = 0u;
static bool IMU_GyroscopeSample_queue_overflow = false;
static Vector3D_t IMU_GyroscopeSample_queue1[8u];
static size_t IMU_GyroscopeSample_queue1_count = 0u;
static size_t IMU_GyroscopeSample_queue1_write_index = 0u;
static bool IMU_GyroscopeSample_queue1_overflow = false;
static Vector3D_t GyroscopeOffsetCompensator_CompensatedAngularSpeeds_queue[32u];
static size_t GyroscopeOffsetCompensator_CompensatedAngularSpeeds_queue_count = 0u;
static size_t GyroscopeOffsetCompensator_CompensatedAngularSpeeds_queue_write_index = 0u;
static bool GyroscopeOffsetCompensator_CompensatedAngularSpeeds_queue_overflow = false;
static bool IMUMovementDetector_IsMoving_variable = true;
static Vector3D_t IMU_AccelerometerSample_queue[32u];
static size_t IMU_AccelerometerSample_queue_count = 0u;
static size_t IMU_AccelerometerSample_queue_write_index = 0u;
static bool IMU_AccelerometerSample_queue_overflow = false;
static Orientation3D_t IMUOrientationEstimator_OrientationEulerDegrees_variable = {
    .pitch = 0.0f,
    .roll  = 0.0f,
    .yaw   = 0.0f
};
static Orientation3D_t IMUOrientationEstimator_OrientationEulerDegrees_variable1 = {
    .pitch = 0.0f,
    .roll  = 0.0f,
    .yaw   = 0.0f
};
static Current_t ADC_MotorCurrent_array[6] = { 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f };
static Voltage_t ADC_MainBatteryVoltage_variable = 0.0f;
static Voltage_t ADC_MotorBatteryVoltage_variable = 0.0f;
static uint8_t ADC_Sensor_ADC_array[4] = { 0u, 0u, 0u, 0u };
static Current_t MotorCurrentFilter_FilteredCurrent_array[6] = { 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f };
static Temperature_t MotorThermalModel_Temperature_array[6] = { 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f };
static BluetoothStatus_t BluetoothStatusObserver_ConnectionStatus_variable = BluetoothStatus_Inactive;
static uint8_t BatteryCalculator_MainBatteryLevel_variable = 0u;
static bool BatteryCalculator_MainBatteryLow_variable = false;
static ChargerState_t BatteryCharger_ChargerState_variable = ChargerState_NotPluggedIn;
static uint8_t BatteryCalculator_MotorBatteryLevel_variable = 0u;
static bool BatteryCalculator_MotorBatteryPresent_variable = false;
static bool BatteryCalculator_MotorBatteryPresent_variable1 = false;
static rgb_t LedDisplayController_Leds_array[16] = {
    (rgb_t){0, 0, 0}, (rgb_t){0, 0, 0}, (rgb_t){0, 0, 0},
    (rgb_t){0, 0, 0}, (rgb_t){0, 0, 0}, (rgb_t){0, 0, 0},
    (rgb_t){0, 0, 0}, (rgb_t){0, 0, 0}, (rgb_t){0, 0, 0},
    (rgb_t){0, 0, 0}, (rgb_t){0, 0, 0}, (rgb_t){0, 0, 0},
    (rgb_t){0, 0, 0}, (rgb_t){0, 0, 0}, (rgb_t){0, 0, 0},
    (rgb_t){0, 0, 0}
};
static uint8_t LedDisplayController_MaxBrightness_variable = 0u;
static rgb_t RingLedDisplay_LedColor_array[12] = {
    (rgb_t){0, 0, 0}, (rgb_t){0, 0, 0}, (rgb_t){0, 0, 0},
    (rgb_t){0, 0, 0}, (rgb_t){0, 0, 0}, (rgb_t){0, 0, 0},
    (rgb_t){0, 0, 0}, (rgb_t){0, 0, 0}, (rgb_t){0, 0, 0},
    (rgb_t){0, 0, 0}, (rgb_t){0, 0, 0}, (rgb_t){0, 0, 0}
};
static MasterStatus_t MasterStatusObserver_MasterStatus_variable = MasterStatus_Unknown;
static int16_t MotorPortHandler_DriveStrength_array[6] = { 0, 0, 0, 0, 0, 0 };
static Current_t MotorPortHandler_MaxAllowedCurrent_array[6] = { 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f };
static Percentage_t MotorDerating_RelativeMotorCurrent_array[6] = { 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f };
static IMU_RawSample_t IMU_RawAccelerometerSample_variable = {
    .x = 0,
    .y = 0,
    .z = 0
};
static IMU_RawSample_t IMU_RawGyroscopeSample_variable = {
    .x = 0,
    .y = 0,
    .z = 0
};
static SlotData_t McuStatusSlots_SlotData_array[16] = {
    {
        .data    = {
            .bytes = NULL,
            .count = 0u
        },
        .version = 0xFFu
    },
    {
        .data    = {
            .bytes = NULL,
            .count = 0u
        },
        .version = 0xFFu
    },
    {
        .data    = {
            .bytes = NULL,
            .count = 0u
        },
        .version = 0xFFu
    },
    {
        .data    = {
            .bytes = NULL,
            .count = 0u
        },
        .version = 0xFFu
    },
    {
        .data    = {
            .bytes = NULL,
            .count = 0u
        },
        .version = 0xFFu
    },
    {
        .data    = {
            .bytes = NULL,
            .count = 0u
        },
        .version = 0xFFu
    },
    {
        .data    = {
            .bytes = NULL,
            .count = 0u
        },
        .version = 0xFFu
    },
    {
        .data    = {
            .bytes = NULL,
            .count = 0u
        },
        .version = 0xFFu
    },
    {
        .data    = {
            .bytes = NULL,
            .count = 0u
        },
        .version = 0xFFu
    },
    {
        .data    = {
            .bytes = NULL,
            .count = 0u
        },
        .version = 0xFFu
    },
    {
        .data    = {
            .bytes = NULL,
            .count = 0u
        },
        .version = 0xFFu
    },
    {
        .data    = {
            .bytes = NULL,
            .count = 0u
        },
        .version = 0xFFu
    },
    {
        .data    = {
            .bytes = NULL,
            .count = 0u
        },
        .version = 0xFFu
    },
    {
        .data    = {
            .bytes = NULL,
            .count = 0u
        },
        .version = 0xFFu
    },
    {
        .data    = {
            .bytes = NULL,
            .count = 0u
        },
        .version = 0xFFu
    },
    {
        .data    = {
            .bytes = NULL,
            .count = 0u
        },
        .version = 0xFFu
    }
};
static rgb_t CommWrapper_LedDisplay_UserFrame_array[12] = {
    (rgb_t){0, 0, 0}, (rgb_t){0, 0, 0}, (rgb_t){0, 0, 0},
    (rgb_t){0, 0, 0}, (rgb_t){0, 0, 0}, (rgb_t){0, 0, 0},
    (rgb_t){0, 0, 0}, (rgb_t){0, 0, 0}, (rgb_t){0, 0, 0},
    (rgb_t){0, 0, 0}, (rgb_t){0, 0, 0}, (rgb_t){0, 0, 0}
};
static RingLedScenario_t CommWrapper_LedDisplay_Scenario_variable = RingLedScenario_ColorWheel;
static bool StartupReasonProvider_IsColdStart_variable = false;

/* SensorPortHandler_SetPortType_async_call */
static AsyncOperationState_t SensorPortHandler_SetPortType_async_call_state = AsyncOperationState_Idle;
static AsyncCommand_t SensorPortHandler_SetPortType_async_call_command = AsyncCommand_None;
static uint8_t SensorPortHandler_SetPortType_async_call_argument_port_idx;
static uint8_t SensorPortHandler_SetPortType_async_call_argument_port_type;
static bool SensorPortHandler_SetPortType_async_call_argument_result;
static void SensorPortHandler_SetPortType_async_call_Update(void);

/* SensorPortHandler_Configure_async_call */
static AsyncOperationState_t SensorPortHandler_Configure_async_call_state = AsyncOperationState_Idle;
static AsyncCommand_t SensorPortHandler_Configure_async_call_command = AsyncCommand_None;
static uint8_t SensorPortHandler_Configure_async_call_argument_port_idx;
static ByteArray_t SensorPortHandler_Configure_async_call_argument_configuration;
static bool SensorPortHandler_Configure_async_call_argument_result;
static void SensorPortHandler_Configure_async_call_Update(void);

/* SensorPortHandler_TestSensorOnPort_async_call */
static AsyncOperationState_t SensorPortHandler_TestSensorOnPort_async_call_state = AsyncOperationState_Idle;
static AsyncCommand_t SensorPortHandler_TestSensorOnPort_async_call_command = AsyncCommand_None;
static uint8_t SensorPortHandler_TestSensorOnPort_async_call_argument_port_idx;
static uint8_t SensorPortHandler_TestSensorOnPort_async_call_argument_port_type;
static TestSensorOnPortResult_t SensorPortHandler_TestSensorOnPort_async_call_argument_result;
static void SensorPortHandler_TestSensorOnPort_async_call_Update(void);
static uint8_t MotorPortHandler_PortCount_variable = 0u;

/* MotorPortHandler_SetPortType_async_call */
static AsyncOperationState_t MotorPortHandler_SetPortType_async_call_state = AsyncOperationState_Idle;
static AsyncCommand_t MotorPortHandler_SetPortType_async_call_command = AsyncCommand_None;
static uint8_t MotorPortHandler_SetPortType_async_call_argument_port_idx;
static uint8_t MotorPortHandler_SetPortType_async_call_argument_port_type;
static bool MotorPortHandler_SetPortType_async_call_argument_result;
static void MotorPortHandler_SetPortType_async_call_Update(void);

/* MotorPortHandler_TestMotorOnPort_async_call */
static AsyncOperationState_t MotorPortHandler_TestMotorOnPort_async_call_state = AsyncOperationState_Idle;
static AsyncCommand_t MotorPortHandler_TestMotorOnPort_async_call_command = AsyncCommand_None;
static uint8_t MotorPortHandler_TestMotorOnPort_async_call_argument_port_idx;
static uint8_t MotorPortHandler_TestMotorOnPort_async_call_argument_test_power;
static uint8_t MotorPortHandler_TestMotorOnPort_async_call_argument_threshold;
static bool MotorPortHandler_TestMotorOnPort_async_call_argument_result;
static void MotorPortHandler_TestMotorOnPort_async_call_Update(void);

/* MotorPortHandler_Configure_async_call */
static AsyncOperationState_t MotorPortHandler_Configure_async_call_state = AsyncOperationState_Idle;
static AsyncCommand_t MotorPortHandler_Configure_async_call_command = AsyncCommand_None;
static uint8_t MotorPortHandler_Configure_async_call_argument_port_idx;
static ByteArray_t MotorPortHandler_Configure_async_call_argument_configuration;
static bool MotorPortHandler_Configure_async_call_argument_result;
static void MotorPortHandler_Configure_async_call_Update(void);
static DriveRequest_t CommWrapper_MotorPorts_DriveRequest_array[6] = {
    {
        .version      = 0u,
        .power_limit  = 0.0f,
        .speed_limit  = 0.0f,
        .request_type = DriveRequest_RequestType_Power,
        .request      = {
            .power = 0
        }
    },
    {
        .version      = 0u,
        .power_limit  = 0.0f,
        .speed_limit  = 0.0f,
        .request_type = DriveRequest_RequestType_Power,
        .request      = {
            .power = 0
        }
    },
    {
        .version      = 0u,
        .power_limit  = 0.0f,
        .speed_limit  = 0.0f,
        .request_type = DriveRequest_RequestType_Power,
        .request      = {
            .power = 0
        }
    },
    {
        .version      = 0u,
        .power_limit  = 0.0f,
        .speed_limit  = 0.0f,
        .request_type = DriveRequest_RequestType_Power,
        .request      = {
            .power = 0
        }
    },
    {
        .version      = 0u,
        .power_limit  = 0.0f,
        .speed_limit  = 0.0f,
        .request_type = DriveRequest_RequestType_Power,
        .request      = {
            .power = 0
        }
    },
    {
        .version      = 0u,
        .power_limit  = 0.0f,
        .speed_limit  = 0.0f,
        .request_type = DriveRequest_RequestType_Power,
        .request      = {
            .power = 0
        }
    }
};

/* RestartManager_RebootToBootloader_async_call */
static AsyncOperationState_t RestartManager_RebootToBootloader_async_call_state = AsyncOperationState_Idle;
static AsyncCommand_t RestartManager_RebootToBootloader_async_call_command = AsyncCommand_None;
static void RestartManager_RebootToBootloader_async_call_Update(void);

void RestartManager_RebootToBootloader_async_call_Update(void)
{
    /* Begin User Code Section: RestartManager/RebootToBootloader:update Start */

    /* End User Code Section: RestartManager/RebootToBootloader:update Start */
    uint32_t primask = __get_PRIMASK();
    __disable_irq();
    AsyncCommand_t command = RestartManager_RebootToBootloader_async_call_command;
    RestartManager_RebootToBootloader_async_call_command = AsyncCommand_None;

    switch (command)
    {
        case AsyncCommand_Start:
            RestartManager_RebootToBootloader_async_call_state = AsyncOperationState_Busy;
            __set_PRIMASK(primask);

            RestartManager_Run_RebootToBootloader();

            RestartManager_RebootToBootloader_async_call_state = AsyncOperationState_Done;
            break;

        case AsyncCommand_Cancel:
            __set_PRIMASK(primask);
            RestartManager_RebootToBootloader_async_call_state = AsyncOperationState_Idle;
            break;

        default:
            __set_PRIMASK(primask);
            break;
    }
    /* Begin User Code Section: RestartManager/RebootToBootloader:update End */

    /* End User Code Section: RestartManager/RebootToBootloader:update End */
}

void SensorPortHandler_Configure_async_call_Update(void)
{
    /* Begin User Code Section: SensorPortHandler/Configure:update Start */

    /* End User Code Section: SensorPortHandler/Configure:update Start */
    uint32_t primask = __get_PRIMASK();
    __disable_irq();
    AsyncCommand_t command = SensorPortHandler_Configure_async_call_command;
    SensorPortHandler_Configure_async_call_command = AsyncCommand_None;

    switch (command)
    {
        case AsyncCommand_Start:
            SensorPortHandler_Configure_async_call_state = AsyncOperationState_Busy;
            __set_PRIMASK(primask);

            SensorPortHandler_Run_Configure(
                SensorPortHandler_Configure_async_call_argument_port_idx,
                SensorPortHandler_Configure_async_call_argument_configuration,
                &SensorPortHandler_Configure_async_call_argument_result);

            SensorPortHandler_Configure_async_call_state = AsyncOperationState_Done;
            break;

        case AsyncCommand_Cancel:
            __set_PRIMASK(primask);
            SensorPortHandler_Configure_async_call_state = AsyncOperationState_Idle;
            break;

        default:
            __set_PRIMASK(primask);
            break;
    }
    /* Begin User Code Section: SensorPortHandler/Configure:update End */

    /* End User Code Section: SensorPortHandler/Configure:update End */
}

void MotorPortHandler_SetPortType_async_call_Update(void)
{
    /* Begin User Code Section: MotorPortHandler/SetPortType:update Start */

    /* End User Code Section: MotorPortHandler/SetPortType:update Start */
    uint32_t primask = __get_PRIMASK();
    __disable_irq();
    AsyncCommand_t command = MotorPortHandler_SetPortType_async_call_command;
    MotorPortHandler_SetPortType_async_call_command = AsyncCommand_None;

    switch (command)
    {
        case AsyncCommand_Start:
            MotorPortHandler_SetPortType_async_call_state = AsyncOperationState_Busy;
            __set_PRIMASK(primask);

            MotorPortHandler_Run_SetPortType(
                MotorPortHandler_SetPortType_async_call_argument_port_idx,
                MotorPortHandler_SetPortType_async_call_argument_port_type,
                &MotorPortHandler_SetPortType_async_call_argument_result);

            MotorPortHandler_SetPortType_async_call_state = AsyncOperationState_Done;
            break;

        case AsyncCommand_Cancel:
            __set_PRIMASK(primask);
            MotorPortHandler_SetPortType_async_call_state = AsyncOperationState_Idle;
            break;

        default:
            __set_PRIMASK(primask);
            break;
    }
    /* Begin User Code Section: MotorPortHandler/SetPortType:update End */

    /* End User Code Section: MotorPortHandler/SetPortType:update End */
}

void MotorPortHandler_Configure_async_call_Update(void)
{
    /* Begin User Code Section: MotorPortHandler/Configure:update Start */

    /* End User Code Section: MotorPortHandler/Configure:update Start */
    uint32_t primask = __get_PRIMASK();
    __disable_irq();
    AsyncCommand_t command = MotorPortHandler_Configure_async_call_command;
    MotorPortHandler_Configure_async_call_command = AsyncCommand_None;

    switch (command)
    {
        case AsyncCommand_Start:
            MotorPortHandler_Configure_async_call_state = AsyncOperationState_Busy;
            __set_PRIMASK(primask);

            MotorPortHandler_Run_Configure(
                MotorPortHandler_Configure_async_call_argument_port_idx,
                MotorPortHandler_Configure_async_call_argument_configuration,
                &MotorPortHandler_Configure_async_call_argument_result);

            MotorPortHandler_Configure_async_call_state = AsyncOperationState_Done;
            break;

        case AsyncCommand_Cancel:
            __set_PRIMASK(primask);
            MotorPortHandler_Configure_async_call_state = AsyncOperationState_Idle;
            break;

        default:
            __set_PRIMASK(primask);
            break;
    }
    /* Begin User Code Section: MotorPortHandler/Configure:update End */

    /* End User Code Section: MotorPortHandler/Configure:update End */
}

void Runtime_RaiseEvent_OnInit(void)
{
    /* Begin User Code Section: Runtime/OnInit:run Start */

    /* End User Code Section: Runtime/OnInit:run Start */
    HardwareCompatibilityChecker_Run_OnInit();
    StartupReasonProvider_Run_OnInit();
    ErrorStorage_Run_OnInit();
    ADC_Run_OnInit();
    MotorCurrentFilter_Run_OnInit();
    BatteryCharger_Run_OnInit();
    LEDController_Run_OnInit();
    BatteryCalculator_Run_OnInit();
    IMU_Run_OnInit();
    HighResolutionTimer_Run_OnInit();
    MasterStatusObserver_Run_OnInit();
    MotorThermalModel_Run_OnInit();
    BluetoothStatusObserver_Run_OnInit();
    RingLedDisplay_Run_OnInit();
    CommunicationObserver_Run_OnInit();
    GyroscopeOffsetCompensator_Run_OnInit();
    MasterCommunicationInterface_Run_OnInit();
    LedDisplayController_Run_OnInit();
    IMUMovementDetector_Run_OnInit();
    IMUOrientationEstimator_Run_OnInit();
    McuStatusSlots_Run_Reset();
    McuStatusCollector_Run_Reset();
    MotorDriver_8833_Run_OnInit();
    /* Begin User Code Section: Runtime/OnInit:run End */

    /* End User Code Section: Runtime/OnInit:run End */
}

void Runtime_RaiseEvent_OnInitDone(void)
{
    /* Begin User Code Section: Runtime/OnInitDone:run Start */

    /* End User Code Section: Runtime/OnInitDone:run Start */
    McuStatusCollector_Run_EnableSlot(14);
    /* Begin User Code Section: Runtime/OnInitDone:run End */

    /* End User Code Section: Runtime/OnInitDone:run End */
}

void Runtime_RaiseEvent_1ms(void)
{
    /* Begin User Code Section: Runtime/1ms:run Start */

    /* End User Code Section: Runtime/1ms:run Start */
    ADC_Run_Update();
    IMU_Run_OnUpdate();
    MotorCurrentFilter_Run_Update();
    MotorThermalModel_Run_OnUpdate();
    McuStatusSlots_Run_Update();
    /* Begin User Code Section: Runtime/1ms:run End */

    /* End User Code Section: Runtime/1ms:run End */
}

void Runtime_RaiseEvent_10ms_offset0(void)
{
    /* Begin User Code Section: Runtime/10ms_offset0:run Start */

    /* End User Code Section: Runtime/10ms_offset0:run Start */
    BatteryCharger_Run_Update();
    WatchdogFeeder_Run_Feed();
    MotorDerating_Run_OnUpdate();
    /* Begin User Code Section: Runtime/10ms_offset0:run End */

    /* End User Code Section: Runtime/10ms_offset0:run End */
}

void Runtime_RaiseEvent_10ms_offset1(void)
{
    /* Begin User Code Section: Runtime/10ms_offset1:run Start */

    /* End User Code Section: Runtime/10ms_offset1:run Start */
    MotorPortHandler_SetPortType_async_call_Update();
    MotorPortHandler_TestMotorOnPort_async_call_Update();
    MotorPortHandler_Configure_async_call_Update();
    IMUMovementDetector_Run_OnUpdate();
    GyroscopeOffsetCompensator_Run_Update();
    IMUOrientationEstimator_Run_OnUpdate();
    /* Begin User Code Section: Runtime/10ms_offset1:run End */

    /* End User Code Section: Runtime/10ms_offset1:run End */
}

void Runtime_RaiseEvent_10ms_offset2(void)
{
    /* Begin User Code Section: Runtime/10ms_offset2:run Start */

    /* End User Code Section: Runtime/10ms_offset2:run Start */
    MotorPortHandler_Run_PortUpdate(4);
    MotorPortHandler_Run_PortUpdate(5);
    /* Begin User Code Section: Runtime/10ms_offset2:run End */

    /* End User Code Section: Runtime/10ms_offset2:run End */
}

void Runtime_RaiseEvent_10ms_offset3(void)
{
    /* Begin User Code Section: Runtime/10ms_offset3:run Start */

    /* End User Code Section: Runtime/10ms_offset3:run Start */
    MotorPortHandler_Run_PortUpdate(1);
    MotorPortHandler_Run_PortUpdate(2);
    /* Begin User Code Section: Runtime/10ms_offset3:run End */

    /* End User Code Section: Runtime/10ms_offset3:run End */
}

void Runtime_RaiseEvent_10ms_offset4(void)
{
    /* Begin User Code Section: Runtime/10ms_offset4:run Start */

    /* End User Code Section: Runtime/10ms_offset4:run Start */
    MotorPortHandler_Run_PortUpdate(0);
    MotorPortHandler_Run_PortUpdate(3);
    /* Begin User Code Section: Runtime/10ms_offset4:run End */

    /* End User Code Section: Runtime/10ms_offset4:run End */
}

void Runtime_RaiseEvent_10ms_offset5(void)
{
    /* Begin User Code Section: Runtime/10ms_offset5:run Start */

    /* End User Code Section: Runtime/10ms_offset5:run Start */
    /* Begin User Code Section: Runtime/10ms_offset5:run End */

    /* End User Code Section: Runtime/10ms_offset5:run End */
}

void Runtime_RaiseEvent_10ms_offset6(void)
{
    /* Begin User Code Section: Runtime/10ms_offset6:run Start */

    /* End User Code Section: Runtime/10ms_offset6:run Start */
    /* Begin User Code Section: Runtime/10ms_offset6:run End */

    /* End User Code Section: Runtime/10ms_offset6:run End */
}

void Runtime_RaiseEvent_10ms_offset7(void)
{
    /* Begin User Code Section: Runtime/10ms_offset7:run Start */

    /* End User Code Section: Runtime/10ms_offset7:run Start */
    /* Begin User Code Section: Runtime/10ms_offset7:run End */

    /* End User Code Section: Runtime/10ms_offset7:run End */
}

void Runtime_RaiseEvent_10ms_offset8(void)
{
    /* Begin User Code Section: Runtime/10ms_offset8:run Start */

    /* End User Code Section: Runtime/10ms_offset8:run Start */
    /* Begin User Code Section: Runtime/10ms_offset8:run End */

    /* End User Code Section: Runtime/10ms_offset8:run End */
}

void Runtime_RaiseEvent_10ms_offset9(void)
{
    /* Begin User Code Section: Runtime/10ms_offset9:run Start */

    /* End User Code Section: Runtime/10ms_offset9:run Start */
    /* Begin User Code Section: Runtime/10ms_offset9:run End */

    /* End User Code Section: Runtime/10ms_offset9:run End */
}

void Runtime_RaiseEvent_20ms_offset0(void)
{
    /* Begin User Code Section: Runtime/20ms_offset0:run Start */

    /* End User Code Section: Runtime/20ms_offset0:run Start */
    RingLedDisplay_Run_Update();
    /* Begin User Code Section: Runtime/20ms_offset0:run End */

    /* End User Code Section: Runtime/20ms_offset0:run End */
}

void Runtime_RaiseEvent_20ms_offset1(void)
{
    /* Begin User Code Section: Runtime/20ms_offset1:run Start */

    /* End User Code Section: Runtime/20ms_offset1:run Start */
    LedDisplayController_Run_Update();
    LEDController_Run_Update();
    /* Begin User Code Section: Runtime/20ms_offset1:run End */

    /* End User Code Section: Runtime/20ms_offset1:run End */
}

void Runtime_RaiseEvent_20ms_offset2(void)
{
    /* Begin User Code Section: Runtime/20ms_offset2:run Start */

    /* End User Code Section: Runtime/20ms_offset2:run Start */
    /* Begin User Code Section: Runtime/20ms_offset2:run End */

    /* End User Code Section: Runtime/20ms_offset2:run End */
}

void Runtime_RaiseEvent_20ms_offset3(void)
{
    /* Begin User Code Section: Runtime/20ms_offset3:run Start */

    /* End User Code Section: Runtime/20ms_offset3:run Start */
    /* Begin User Code Section: Runtime/20ms_offset3:run End */

    /* End User Code Section: Runtime/20ms_offset3:run End */
}

void Runtime_RaiseEvent_20ms_offset4(void)
{
    /* Begin User Code Section: Runtime/20ms_offset4:run Start */

    /* End User Code Section: Runtime/20ms_offset4:run Start */
    SensorPortHandler_SetPortType_async_call_Update();
    SensorPortHandler_Configure_async_call_Update();
    SensorPortHandler_TestSensorOnPort_async_call_Update();
    /* Begin User Code Section: Runtime/20ms_offset4:run End */

    /* End User Code Section: Runtime/20ms_offset4:run End */
}

void Runtime_RaiseEvent_20ms_offset5(void)
{
    /* Begin User Code Section: Runtime/20ms_offset5:run Start */

    /* End User Code Section: Runtime/20ms_offset5:run Start */
    SensorPortHandler_Run_PortUpdate(0);
    /* Begin User Code Section: Runtime/20ms_offset5:run End */

    /* End User Code Section: Runtime/20ms_offset5:run End */
}

void Runtime_RaiseEvent_20ms_offset6(void)
{
    /* Begin User Code Section: Runtime/20ms_offset6:run Start */

    /* End User Code Section: Runtime/20ms_offset6:run Start */
    SensorPortHandler_Run_PortUpdate(1);
    /* Begin User Code Section: Runtime/20ms_offset6:run End */

    /* End User Code Section: Runtime/20ms_offset6:run End */
}

void Runtime_RaiseEvent_20ms_offset7(void)
{
    /* Begin User Code Section: Runtime/20ms_offset7:run Start */

    /* End User Code Section: Runtime/20ms_offset7:run Start */
    SensorPortHandler_Run_PortUpdate(2);
    /* Begin User Code Section: Runtime/20ms_offset7:run End */

    /* End User Code Section: Runtime/20ms_offset7:run End */
}

void Runtime_RaiseEvent_20ms_offset8(void)
{
    /* Begin User Code Section: Runtime/20ms_offset8:run Start */

    /* End User Code Section: Runtime/20ms_offset8:run Start */
    SensorPortHandler_Run_PortUpdate(3);
    /* Begin User Code Section: Runtime/20ms_offset8:run End */

    /* End User Code Section: Runtime/20ms_offset8:run End */
}

void Runtime_RaiseEvent_20ms_offset9(void)
{
    /* Begin User Code Section: Runtime/20ms_offset9:run Start */

    /* End User Code Section: Runtime/20ms_offset9:run Start */
    /* Begin User Code Section: Runtime/20ms_offset9:run End */

    /* End User Code Section: Runtime/20ms_offset9:run End */
}

void Runtime_RaiseEvent_20ms_offset10(void)
{
    /* Begin User Code Section: Runtime/20ms_offset10:run Start */

    /* End User Code Section: Runtime/20ms_offset10:run Start */
    /* Begin User Code Section: Runtime/20ms_offset10:run End */

    /* End User Code Section: Runtime/20ms_offset10:run End */
}

void Runtime_RaiseEvent_20ms_offset11(void)
{
    /* Begin User Code Section: Runtime/20ms_offset11:run Start */

    /* End User Code Section: Runtime/20ms_offset11:run Start */
    /* Begin User Code Section: Runtime/20ms_offset11:run End */

    /* End User Code Section: Runtime/20ms_offset11:run End */
}

void Runtime_RaiseEvent_20ms_offset12(void)
{
    /* Begin User Code Section: Runtime/20ms_offset12:run Start */

    /* End User Code Section: Runtime/20ms_offset12:run Start */
    /* Begin User Code Section: Runtime/20ms_offset12:run End */

    /* End User Code Section: Runtime/20ms_offset12:run End */
}

void Runtime_RaiseEvent_20ms_offset13(void)
{
    /* Begin User Code Section: Runtime/20ms_offset13:run Start */

    /* End User Code Section: Runtime/20ms_offset13:run Start */
    /* Begin User Code Section: Runtime/20ms_offset13:run End */

    /* End User Code Section: Runtime/20ms_offset13:run End */
}

void Runtime_RaiseEvent_20ms_offset14(void)
{
    /* Begin User Code Section: Runtime/20ms_offset14:run Start */

    /* End User Code Section: Runtime/20ms_offset14:run Start */
    /* Begin User Code Section: Runtime/20ms_offset14:run End */

    /* End User Code Section: Runtime/20ms_offset14:run End */
}

void Runtime_RaiseEvent_20ms_offset15(void)
{
    /* Begin User Code Section: Runtime/20ms_offset15:run Start */

    /* End User Code Section: Runtime/20ms_offset15:run Start */
    /* Begin User Code Section: Runtime/20ms_offset15:run End */

    /* End User Code Section: Runtime/20ms_offset15:run End */
}

void Runtime_RaiseEvent_20ms_offset16(void)
{
    /* Begin User Code Section: Runtime/20ms_offset16:run Start */

    /* End User Code Section: Runtime/20ms_offset16:run Start */
    /* Begin User Code Section: Runtime/20ms_offset16:run End */

    /* End User Code Section: Runtime/20ms_offset16:run End */
}

void Runtime_RaiseEvent_20ms_offset17(void)
{
    /* Begin User Code Section: Runtime/20ms_offset17:run Start */

    /* End User Code Section: Runtime/20ms_offset17:run Start */
    /* Begin User Code Section: Runtime/20ms_offset17:run End */

    /* End User Code Section: Runtime/20ms_offset17:run End */
}

void Runtime_RaiseEvent_20ms_offset18(void)
{
    /* Begin User Code Section: Runtime/20ms_offset18:run Start */

    /* End User Code Section: Runtime/20ms_offset18:run Start */
    /* Begin User Code Section: Runtime/20ms_offset18:run End */

    /* End User Code Section: Runtime/20ms_offset18:run End */
}

void Runtime_RaiseEvent_20ms_offset19(void)
{
    /* Begin User Code Section: Runtime/20ms_offset19:run Start */

    /* End User Code Section: Runtime/20ms_offset19:run Start */
    /* Begin User Code Section: Runtime/20ms_offset19:run End */

    /* End User Code Section: Runtime/20ms_offset19:run End */
}

void Runtime_RaiseEvent_100ms(void)
{
    /* Begin User Code Section: Runtime/100ms:run Start */

    /* End User Code Section: Runtime/100ms:run Start */
    BatteryCalculator_Run_Update();
    MasterStatusObserver_Run_Update();
    /* Begin User Code Section: Runtime/100ms:run End */

    /* End User Code Section: Runtime/100ms:run End */
}

void HardwareCompatibilityChecker_RaiseEvent_OnIncompatibleHardware(void)
{
    /* Begin User Code Section: HardwareCompatibilityChecker/OnIncompatibleHardware:run Start */

    /* End User Code Section: HardwareCompatibilityChecker/OnIncompatibleHardware:run Start */
    RestartManager_Run_RebootToBootloader();
    /* Begin User Code Section: HardwareCompatibilityChecker/OnIncompatibleHardware:run End */

    /* End User Code Section: HardwareCompatibilityChecker/OnIncompatibleHardware:run End */
}

void CommunicationObserver_RaiseEvent_ErrorLimitReached(void)
{
    /* Begin User Code Section: CommunicationObserver/ErrorLimitReached:run Start */

    /* End User Code Section: CommunicationObserver/ErrorLimitReached:run Start */
    RestartManager_Run_Reset();
    /* Begin User Code Section: CommunicationObserver/ErrorLimitReached:run End */

    /* End User Code Section: CommunicationObserver/ErrorLimitReached:run End */
}

void MasterCommunicationInterface_RaiseEvent_RxTimeout(void)
{
    /* Begin User Code Section: MasterCommunicationInterface/RxTimeout:run Start */

    /* End User Code Section: MasterCommunicationInterface/RxTimeout:run Start */
    CommunicationObserver_Run_OnMessageMissed();
    /* Begin User Code Section: MasterCommunicationInterface/RxTimeout:run End */

    /* End User Code Section: MasterCommunicationInterface/RxTimeout:run End */
}

void MasterCommunicationInterface_RaiseEvent_OnMessageReceived(ConstByteArray_t message)
{
    /* Begin User Code Section: MasterCommunicationInterface/OnMessageReceived:run Start */

    /* End User Code Section: MasterCommunicationInterface/OnMessageReceived:run Start */
    CommunicationObserver_Run_OnMessageReceived();
    MasterCommunication_Run_HandleCommand(message);
    /* Begin User Code Section: MasterCommunicationInterface/OnMessageReceived:run End */

    /* End User Code Section: MasterCommunicationInterface/OnMessageReceived:run End */
}

void CommunicationObserver_RaiseEvent_FirstMessageReceived(void)
{
    /* Begin User Code Section: CommunicationObserver/FirstMessageReceived:run Start */

    /* End User Code Section: CommunicationObserver/FirstMessageReceived:run Start */
    CommWrapper_LedDisplay_Run_Reset();
    RingLedDisplay_Run_OnMasterStarted();
    /* Begin User Code Section: CommunicationObserver/FirstMessageReceived:run End */

    /* End User Code Section: CommunicationObserver/FirstMessageReceived:run End */
}

void ConfigEventProvider_RaiseEvent_OnConfigEventReceived(void)
{
    /* Begin User Code Section: ConfigEventProvider/OnConfigEventReceived:run Start */

    /* End User Code Section: ConfigEventProvider/OnConfigEventReceived:run Start */
    /* Begin User Code Section: ConfigEventProvider/OnConfigEventReceived:run End */

    /* End User Code Section: ConfigEventProvider/OnConfigEventReceived:run End */
}

void SensorPortHandler_SetPortType_async_call_Update(void)
{
    /* Begin User Code Section: SensorPortHandler/SetPortType:update Start */

    /* End User Code Section: SensorPortHandler/SetPortType:update Start */
    uint32_t primask = __get_PRIMASK();
    __disable_irq();
    AsyncCommand_t command = SensorPortHandler_SetPortType_async_call_command;
    SensorPortHandler_SetPortType_async_call_command = AsyncCommand_None;

    switch (command)
    {
        case AsyncCommand_Start:
            SensorPortHandler_SetPortType_async_call_state = AsyncOperationState_Busy;
            __set_PRIMASK(primask);

            AsyncResult_t result = SensorPortHandler_AsyncRunnable_SetPortType(command,
                SensorPortHandler_SetPortType_async_call_argument_port_idx,
                SensorPortHandler_SetPortType_async_call_argument_port_type,
                &SensorPortHandler_SetPortType_async_call_argument_result);
            switch (result)
            {
                case AsyncResult_Ok:
                    SensorPortHandler_SetPortType_async_call_state = AsyncOperationState_Done;
                    break;

                case AsyncResult_Pending:
                    break;

                default:
                    ASSERT(0);
                    break;
            }
            break;

        case AsyncCommand_None:
            if (SensorPortHandler_SetPortType_async_call_state == AsyncOperationState_Busy)
            {
                __set_PRIMASK(primask);

                AsyncResult_t result = SensorPortHandler_AsyncRunnable_SetPortType(command,
                SensorPortHandler_SetPortType_async_call_argument_port_idx,
                SensorPortHandler_SetPortType_async_call_argument_port_type,
                &SensorPortHandler_SetPortType_async_call_argument_result);
                switch (result)
                {
                    case AsyncResult_Ok:
                        SensorPortHandler_SetPortType_async_call_state = AsyncOperationState_Done;
                        break;

                    case AsyncResult_Pending:
                        break;

                    default:
                        ASSERT(0);
                        break;
                }
            }
            else
            {
                __set_PRIMASK(primask);
            }
            break;

        case AsyncCommand_Cancel:
            if (SensorPortHandler_SetPortType_async_call_state == AsyncOperationState_Busy)
            {
                __set_PRIMASK(primask);
                (void) SensorPortHandler_AsyncRunnable_SetPortType(AsyncCommand_Cancel,
                SensorPortHandler_SetPortType_async_call_argument_port_idx,
                SensorPortHandler_SetPortType_async_call_argument_port_type,
                &SensorPortHandler_SetPortType_async_call_argument_result);
            }
            else
            {
                __set_PRIMASK(primask);
            }
            SensorPortHandler_SetPortType_async_call_state = AsyncOperationState_Idle;
            break;

        default:
            __set_PRIMASK(primask);
            ASSERT(0);
            break;
    }

    /* Begin User Code Section: SensorPortHandler/SetPortType:update End */

    /* End User Code Section: SensorPortHandler/SetPortType:update End */
}

AsyncOperationState_t CommWrapper_SensorPorts_Async_SetPortType_Call(uint8_t port_idx, uint8_t port_type)
{
    /* Begin User Code Section: CommWrapper_SensorPorts/SetPortType:async_call Start */

    /* End User Code Section: CommWrapper_SensorPorts/SetPortType:async_call Start */
    AsyncOperationState_t returned_state = AsyncOperationState_Busy;
    SensorPortHandler_SetPortType_async_call_command = AsyncCommand_None;
    uint32_t primask = __get_PRIMASK();
    __disable_irq();
    if (SensorPortHandler_SetPortType_async_call_state == AsyncOperationState_Idle || SensorPortHandler_SetPortType_async_call_state == AsyncOperationState_Done)
    {
        SensorPortHandler_SetPortType_async_call_state = AsyncOperationState_Started;
        __set_PRIMASK(primask);

        SensorPortHandler_SetPortType_async_call_argument_port_idx = port_idx;
        SensorPortHandler_SetPortType_async_call_argument_port_type = port_type;

        returned_state = AsyncOperationState_Started;
        SensorPortHandler_SetPortType_async_call_command = AsyncCommand_Start;
    }
    else
    {
        __set_PRIMASK(primask);
    }
    return returned_state;
    /* Begin User Code Section: CommWrapper_SensorPorts/SetPortType:async_call End */

    /* End User Code Section: CommWrapper_SensorPorts/SetPortType:async_call End */
}

AsyncOperationState_t CommWrapper_SensorPorts_Async_SetPortType_GetResult(bool* result)
{
    /* Begin User Code Section: CommWrapper_SensorPorts/SetPortType:get_result Start */

    /* End User Code Section: CommWrapper_SensorPorts/SetPortType:get_result Start */
    AsyncOperationState_t returned_state;
    uint32_t primask = __get_PRIMASK();
    __disable_irq();
    switch (SensorPortHandler_SetPortType_async_call_state)
    {
        case AsyncOperationState_Done:
            if (result)
            {
                *result = SensorPortHandler_SetPortType_async_call_argument_result;
            }
            SensorPortHandler_SetPortType_async_call_state = AsyncOperationState_Idle;
            __set_PRIMASK(primask);
            returned_state = AsyncOperationState_Done;
            break;

        case AsyncOperationState_Started:
            __set_PRIMASK(primask);
            returned_state = AsyncOperationState_Busy;
            break;

        default:
            __set_PRIMASK(primask);
            returned_state = SensorPortHandler_SetPortType_async_call_state;
            break;
    }
    return returned_state;
    /* Begin User Code Section: CommWrapper_SensorPorts/SetPortType:get_result End */

    /* End User Code Section: CommWrapper_SensorPorts/SetPortType:get_result End */
}

void CommWrapper_SensorPorts_Async_SetPortType_Cancel(void)
{
    /* Begin User Code Section: CommWrapper_SensorPorts/SetPortType:cancel Start */

    /* End User Code Section: CommWrapper_SensorPorts/SetPortType:cancel Start */
    SensorPortHandler_SetPortType_async_call_command = AsyncCommand_Cancel;
    /* Begin User Code Section: CommWrapper_SensorPorts/SetPortType:cancel End */

    /* End User Code Section: CommWrapper_SensorPorts/SetPortType:cancel End */
}

AsyncOperationState_t CommWrapper_SensorPorts_Async_SetPortConfig_Call(uint8_t port_idx, ByteArray_t configuration)
{
    /* Begin User Code Section: CommWrapper_SensorPorts/SetPortConfig:async_call Start */

    /* End User Code Section: CommWrapper_SensorPorts/SetPortConfig:async_call Start */
    AsyncOperationState_t returned_state = AsyncOperationState_Busy;
    SensorPortHandler_Configure_async_call_command = AsyncCommand_None;
    uint32_t primask = __get_PRIMASK();
    __disable_irq();
    if (SensorPortHandler_Configure_async_call_state == AsyncOperationState_Idle || SensorPortHandler_Configure_async_call_state == AsyncOperationState_Done)
    {
        SensorPortHandler_Configure_async_call_state = AsyncOperationState_Started;
        __set_PRIMASK(primask);

        SensorPortHandler_Configure_async_call_argument_port_idx = port_idx;
        SensorPortHandler_Configure_async_call_argument_configuration = configuration;

        returned_state = AsyncOperationState_Started;
        SensorPortHandler_Configure_async_call_command = AsyncCommand_Start;
    }
    else
    {
        __set_PRIMASK(primask);
    }
    return returned_state;
    /* Begin User Code Section: CommWrapper_SensorPorts/SetPortConfig:async_call End */

    /* End User Code Section: CommWrapper_SensorPorts/SetPortConfig:async_call End */
}

AsyncOperationState_t CommWrapper_SensorPorts_Async_SetPortConfig_GetResult(bool* result)
{
    /* Begin User Code Section: CommWrapper_SensorPorts/SetPortConfig:get_result Start */

    /* End User Code Section: CommWrapper_SensorPorts/SetPortConfig:get_result Start */
    AsyncOperationState_t returned_state;
    uint32_t primask = __get_PRIMASK();
    __disable_irq();
    switch (SensorPortHandler_Configure_async_call_state)
    {
        case AsyncOperationState_Done:
            if (result)
            {
                *result = SensorPortHandler_Configure_async_call_argument_result;
            }
            SensorPortHandler_Configure_async_call_state = AsyncOperationState_Idle;
            __set_PRIMASK(primask);
            returned_state = AsyncOperationState_Done;
            break;

        case AsyncOperationState_Started:
            __set_PRIMASK(primask);
            returned_state = AsyncOperationState_Busy;
            break;

        default:
            __set_PRIMASK(primask);
            returned_state = SensorPortHandler_Configure_async_call_state;
            break;
    }
    return returned_state;
    /* Begin User Code Section: CommWrapper_SensorPorts/SetPortConfig:get_result End */

    /* End User Code Section: CommWrapper_SensorPorts/SetPortConfig:get_result End */
}

void CommWrapper_SensorPorts_Async_SetPortConfig_Cancel(void)
{
    /* Begin User Code Section: CommWrapper_SensorPorts/SetPortConfig:cancel Start */

    /* End User Code Section: CommWrapper_SensorPorts/SetPortConfig:cancel Start */
    SensorPortHandler_Configure_async_call_command = AsyncCommand_Cancel;
    /* Begin User Code Section: CommWrapper_SensorPorts/SetPortConfig:cancel End */

    /* End User Code Section: CommWrapper_SensorPorts/SetPortConfig:cancel End */
}

void SensorPortHandler_TestSensorOnPort_async_call_Update(void)
{
    /* Begin User Code Section: SensorPortHandler/TestSensorOnPort:update Start */

    /* End User Code Section: SensorPortHandler/TestSensorOnPort:update Start */
    uint32_t primask = __get_PRIMASK();
    __disable_irq();
    AsyncCommand_t command = SensorPortHandler_TestSensorOnPort_async_call_command;
    SensorPortHandler_TestSensorOnPort_async_call_command = AsyncCommand_None;

    switch (command)
    {
        case AsyncCommand_Start:
            SensorPortHandler_TestSensorOnPort_async_call_state = AsyncOperationState_Busy;
            __set_PRIMASK(primask);

            AsyncResult_t result = SensorPortHandler_AsyncRunnable_TestSensorOnPort(command,
                SensorPortHandler_TestSensorOnPort_async_call_argument_port_idx,
                SensorPortHandler_TestSensorOnPort_async_call_argument_port_type,
                &SensorPortHandler_TestSensorOnPort_async_call_argument_result);
            switch (result)
            {
                case AsyncResult_Ok:
                    SensorPortHandler_TestSensorOnPort_async_call_state = AsyncOperationState_Done;
                    break;

                case AsyncResult_Pending:
                    break;

                default:
                    ASSERT(0);
                    break;
            }
            break;

        case AsyncCommand_None:
            if (SensorPortHandler_TestSensorOnPort_async_call_state == AsyncOperationState_Busy)
            {
                __set_PRIMASK(primask);

                AsyncResult_t result = SensorPortHandler_AsyncRunnable_TestSensorOnPort(command,
                SensorPortHandler_TestSensorOnPort_async_call_argument_port_idx,
                SensorPortHandler_TestSensorOnPort_async_call_argument_port_type,
                &SensorPortHandler_TestSensorOnPort_async_call_argument_result);
                switch (result)
                {
                    case AsyncResult_Ok:
                        SensorPortHandler_TestSensorOnPort_async_call_state = AsyncOperationState_Done;
                        break;

                    case AsyncResult_Pending:
                        break;

                    default:
                        ASSERT(0);
                        break;
                }
            }
            else
            {
                __set_PRIMASK(primask);
            }
            break;

        case AsyncCommand_Cancel:
            if (SensorPortHandler_TestSensorOnPort_async_call_state == AsyncOperationState_Busy)
            {
                __set_PRIMASK(primask);
                (void) SensorPortHandler_AsyncRunnable_TestSensorOnPort(AsyncCommand_Cancel,
                SensorPortHandler_TestSensorOnPort_async_call_argument_port_idx,
                SensorPortHandler_TestSensorOnPort_async_call_argument_port_type,
                &SensorPortHandler_TestSensorOnPort_async_call_argument_result);
            }
            else
            {
                __set_PRIMASK(primask);
            }
            SensorPortHandler_TestSensorOnPort_async_call_state = AsyncOperationState_Idle;
            break;

        default:
            __set_PRIMASK(primask);
            ASSERT(0);
            break;
    }

    /* Begin User Code Section: SensorPortHandler/TestSensorOnPort:update End */

    /* End User Code Section: SensorPortHandler/TestSensorOnPort:update End */
}

AsyncOperationState_t CommWrapper_SensorPorts_Async_TestSensorOnPort_Call(uint8_t port_idx, uint8_t port_type)
{
    /* Begin User Code Section: CommWrapper_SensorPorts/TestSensorOnPort:async_call Start */

    /* End User Code Section: CommWrapper_SensorPorts/TestSensorOnPort:async_call Start */
    AsyncOperationState_t returned_state = AsyncOperationState_Busy;
    SensorPortHandler_TestSensorOnPort_async_call_command = AsyncCommand_None;
    uint32_t primask = __get_PRIMASK();
    __disable_irq();
    if (SensorPortHandler_TestSensorOnPort_async_call_state == AsyncOperationState_Idle || SensorPortHandler_TestSensorOnPort_async_call_state == AsyncOperationState_Done)
    {
        SensorPortHandler_TestSensorOnPort_async_call_state = AsyncOperationState_Started;
        __set_PRIMASK(primask);

        SensorPortHandler_TestSensorOnPort_async_call_argument_port_idx = port_idx;
        SensorPortHandler_TestSensorOnPort_async_call_argument_port_type = port_type;

        returned_state = AsyncOperationState_Started;
        SensorPortHandler_TestSensorOnPort_async_call_command = AsyncCommand_Start;
    }
    else
    {
        __set_PRIMASK(primask);
    }
    return returned_state;
    /* Begin User Code Section: CommWrapper_SensorPorts/TestSensorOnPort:async_call End */

    /* End User Code Section: CommWrapper_SensorPorts/TestSensorOnPort:async_call End */
}

AsyncOperationState_t CommWrapper_SensorPorts_Async_TestSensorOnPort_GetResult(TestSensorOnPortResult_t* result)
{
    /* Begin User Code Section: CommWrapper_SensorPorts/TestSensorOnPort:get_result Start */

    /* End User Code Section: CommWrapper_SensorPorts/TestSensorOnPort:get_result Start */
    AsyncOperationState_t returned_state;
    uint32_t primask = __get_PRIMASK();
    __disable_irq();
    switch (SensorPortHandler_TestSensorOnPort_async_call_state)
    {
        case AsyncOperationState_Done:
            if (result)
            {
                *result = SensorPortHandler_TestSensorOnPort_async_call_argument_result;
            }
            SensorPortHandler_TestSensorOnPort_async_call_state = AsyncOperationState_Idle;
            __set_PRIMASK(primask);
            returned_state = AsyncOperationState_Done;
            break;

        case AsyncOperationState_Started:
            __set_PRIMASK(primask);
            returned_state = AsyncOperationState_Busy;
            break;

        default:
            __set_PRIMASK(primask);
            returned_state = SensorPortHandler_TestSensorOnPort_async_call_state;
            break;
    }
    return returned_state;
    /* Begin User Code Section: CommWrapper_SensorPorts/TestSensorOnPort:get_result End */

    /* End User Code Section: CommWrapper_SensorPorts/TestSensorOnPort:get_result End */
}

void CommWrapper_SensorPorts_Async_TestSensorOnPort_Cancel(void)
{
    /* Begin User Code Section: CommWrapper_SensorPorts/TestSensorOnPort:cancel Start */

    /* End User Code Section: CommWrapper_SensorPorts/TestSensorOnPort:cancel Start */
    SensorPortHandler_TestSensorOnPort_async_call_command = AsyncCommand_Cancel;
    /* Begin User Code Section: CommWrapper_SensorPorts/TestSensorOnPort:cancel End */

    /* End User Code Section: CommWrapper_SensorPorts/TestSensorOnPort:cancel End */
}

AsyncOperationState_t CommWrapper_MotorPorts_Async_SetPortType_Call(uint8_t port_idx, uint8_t port_type)
{
    /* Begin User Code Section: CommWrapper_MotorPorts/SetPortType:async_call Start */

    /* End User Code Section: CommWrapper_MotorPorts/SetPortType:async_call Start */
    AsyncOperationState_t returned_state = AsyncOperationState_Busy;
    MotorPortHandler_SetPortType_async_call_command = AsyncCommand_None;
    uint32_t primask = __get_PRIMASK();
    __disable_irq();
    if (MotorPortHandler_SetPortType_async_call_state == AsyncOperationState_Idle || MotorPortHandler_SetPortType_async_call_state == AsyncOperationState_Done)
    {
        MotorPortHandler_SetPortType_async_call_state = AsyncOperationState_Started;
        __set_PRIMASK(primask);

        MotorPortHandler_SetPortType_async_call_argument_port_idx = port_idx;
        MotorPortHandler_SetPortType_async_call_argument_port_type = port_type;

        returned_state = AsyncOperationState_Started;
        MotorPortHandler_SetPortType_async_call_command = AsyncCommand_Start;
    }
    else
    {
        __set_PRIMASK(primask);
    }
    return returned_state;
    /* Begin User Code Section: CommWrapper_MotorPorts/SetPortType:async_call End */

    /* End User Code Section: CommWrapper_MotorPorts/SetPortType:async_call End */
}

AsyncOperationState_t CommWrapper_MotorPorts_Async_SetPortType_GetResult(bool* result)
{
    /* Begin User Code Section: CommWrapper_MotorPorts/SetPortType:get_result Start */

    /* End User Code Section: CommWrapper_MotorPorts/SetPortType:get_result Start */
    AsyncOperationState_t returned_state;
    uint32_t primask = __get_PRIMASK();
    __disable_irq();
    switch (MotorPortHandler_SetPortType_async_call_state)
    {
        case AsyncOperationState_Done:
            if (result)
            {
                *result = MotorPortHandler_SetPortType_async_call_argument_result;
            }
            MotorPortHandler_SetPortType_async_call_state = AsyncOperationState_Idle;
            __set_PRIMASK(primask);
            returned_state = AsyncOperationState_Done;
            break;

        case AsyncOperationState_Started:
            __set_PRIMASK(primask);
            returned_state = AsyncOperationState_Busy;
            break;

        default:
            __set_PRIMASK(primask);
            returned_state = MotorPortHandler_SetPortType_async_call_state;
            break;
    }
    return returned_state;
    /* Begin User Code Section: CommWrapper_MotorPorts/SetPortType:get_result End */

    /* End User Code Section: CommWrapper_MotorPorts/SetPortType:get_result End */
}

void CommWrapper_MotorPorts_Async_SetPortType_Cancel(void)
{
    /* Begin User Code Section: CommWrapper_MotorPorts/SetPortType:cancel Start */

    /* End User Code Section: CommWrapper_MotorPorts/SetPortType:cancel Start */
    MotorPortHandler_SetPortType_async_call_command = AsyncCommand_Cancel;
    /* Begin User Code Section: CommWrapper_MotorPorts/SetPortType:cancel End */

    /* End User Code Section: CommWrapper_MotorPorts/SetPortType:cancel End */
}

void MotorPortHandler_TestMotorOnPort_async_call_Update(void)
{
    /* Begin User Code Section: MotorPortHandler/TestMotorOnPort:update Start */

    /* End User Code Section: MotorPortHandler/TestMotorOnPort:update Start */
    uint32_t primask = __get_PRIMASK();
    __disable_irq();
    AsyncCommand_t command = MotorPortHandler_TestMotorOnPort_async_call_command;
    MotorPortHandler_TestMotorOnPort_async_call_command = AsyncCommand_None;

    switch (command)
    {
        case AsyncCommand_Start:
            MotorPortHandler_TestMotorOnPort_async_call_state = AsyncOperationState_Busy;
            __set_PRIMASK(primask);

            AsyncResult_t result = MotorPortHandler_AsyncRunnable_TestMotorOnPort(command,
                MotorPortHandler_TestMotorOnPort_async_call_argument_port_idx,
                MotorPortHandler_TestMotorOnPort_async_call_argument_test_power,
                MotorPortHandler_TestMotorOnPort_async_call_argument_threshold,
                &MotorPortHandler_TestMotorOnPort_async_call_argument_result);
            switch (result)
            {
                case AsyncResult_Ok:
                    MotorPortHandler_TestMotorOnPort_async_call_state = AsyncOperationState_Done;
                    break;

                case AsyncResult_Pending:
                    break;

                default:
                    ASSERT(0);
                    break;
            }
            break;

        case AsyncCommand_None:
            if (MotorPortHandler_TestMotorOnPort_async_call_state == AsyncOperationState_Busy)
            {
                __set_PRIMASK(primask);

                AsyncResult_t result = MotorPortHandler_AsyncRunnable_TestMotorOnPort(command,
                MotorPortHandler_TestMotorOnPort_async_call_argument_port_idx,
                MotorPortHandler_TestMotorOnPort_async_call_argument_test_power,
                MotorPortHandler_TestMotorOnPort_async_call_argument_threshold,
                &MotorPortHandler_TestMotorOnPort_async_call_argument_result);
                switch (result)
                {
                    case AsyncResult_Ok:
                        MotorPortHandler_TestMotorOnPort_async_call_state = AsyncOperationState_Done;
                        break;

                    case AsyncResult_Pending:
                        break;

                    default:
                        ASSERT(0);
                        break;
                }
            }
            else
            {
                __set_PRIMASK(primask);
            }
            break;

        case AsyncCommand_Cancel:
            if (MotorPortHandler_TestMotorOnPort_async_call_state == AsyncOperationState_Busy)
            {
                __set_PRIMASK(primask);
                (void) MotorPortHandler_AsyncRunnable_TestMotorOnPort(AsyncCommand_Cancel,
                MotorPortHandler_TestMotorOnPort_async_call_argument_port_idx,
                MotorPortHandler_TestMotorOnPort_async_call_argument_test_power,
                MotorPortHandler_TestMotorOnPort_async_call_argument_threshold,
                &MotorPortHandler_TestMotorOnPort_async_call_argument_result);
            }
            else
            {
                __set_PRIMASK(primask);
            }
            MotorPortHandler_TestMotorOnPort_async_call_state = AsyncOperationState_Idle;
            break;

        default:
            __set_PRIMASK(primask);
            ASSERT(0);
            break;
    }

    /* Begin User Code Section: MotorPortHandler/TestMotorOnPort:update End */

    /* End User Code Section: MotorPortHandler/TestMotorOnPort:update End */
}

AsyncOperationState_t CommWrapper_MotorPorts_Async_TestMotorOnPort_Call(uint8_t port_idx, uint8_t test_power, uint8_t threshold)
{
    /* Begin User Code Section: CommWrapper_MotorPorts/TestMotorOnPort:async_call Start */

    /* End User Code Section: CommWrapper_MotorPorts/TestMotorOnPort:async_call Start */
    AsyncOperationState_t returned_state = AsyncOperationState_Busy;
    MotorPortHandler_TestMotorOnPort_async_call_command = AsyncCommand_None;
    uint32_t primask = __get_PRIMASK();
    __disable_irq();
    if (MotorPortHandler_TestMotorOnPort_async_call_state == AsyncOperationState_Idle || MotorPortHandler_TestMotorOnPort_async_call_state == AsyncOperationState_Done)
    {
        MotorPortHandler_TestMotorOnPort_async_call_state = AsyncOperationState_Started;
        __set_PRIMASK(primask);

        MotorPortHandler_TestMotorOnPort_async_call_argument_port_idx = port_idx;
        MotorPortHandler_TestMotorOnPort_async_call_argument_test_power = test_power;
        MotorPortHandler_TestMotorOnPort_async_call_argument_threshold = threshold;

        returned_state = AsyncOperationState_Started;
        MotorPortHandler_TestMotorOnPort_async_call_command = AsyncCommand_Start;
    }
    else
    {
        __set_PRIMASK(primask);
    }
    return returned_state;
    /* Begin User Code Section: CommWrapper_MotorPorts/TestMotorOnPort:async_call End */

    /* End User Code Section: CommWrapper_MotorPorts/TestMotorOnPort:async_call End */
}

AsyncOperationState_t CommWrapper_MotorPorts_Async_TestMotorOnPort_GetResult(bool* result)
{
    /* Begin User Code Section: CommWrapper_MotorPorts/TestMotorOnPort:get_result Start */

    /* End User Code Section: CommWrapper_MotorPorts/TestMotorOnPort:get_result Start */
    AsyncOperationState_t returned_state;
    uint32_t primask = __get_PRIMASK();
    __disable_irq();
    switch (MotorPortHandler_TestMotorOnPort_async_call_state)
    {
        case AsyncOperationState_Done:
            if (result)
            {
                *result = MotorPortHandler_TestMotorOnPort_async_call_argument_result;
            }
            MotorPortHandler_TestMotorOnPort_async_call_state = AsyncOperationState_Idle;
            __set_PRIMASK(primask);
            returned_state = AsyncOperationState_Done;
            break;

        case AsyncOperationState_Started:
            __set_PRIMASK(primask);
            returned_state = AsyncOperationState_Busy;
            break;

        default:
            __set_PRIMASK(primask);
            returned_state = MotorPortHandler_TestMotorOnPort_async_call_state;
            break;
    }
    return returned_state;
    /* Begin User Code Section: CommWrapper_MotorPorts/TestMotorOnPort:get_result End */

    /* End User Code Section: CommWrapper_MotorPorts/TestMotorOnPort:get_result End */
}

void CommWrapper_MotorPorts_Async_TestMotorOnPort_Cancel(void)
{
    /* Begin User Code Section: CommWrapper_MotorPorts/TestMotorOnPort:cancel Start */

    /* End User Code Section: CommWrapper_MotorPorts/TestMotorOnPort:cancel Start */
    MotorPortHandler_TestMotorOnPort_async_call_command = AsyncCommand_Cancel;
    /* Begin User Code Section: CommWrapper_MotorPorts/TestMotorOnPort:cancel End */

    /* End User Code Section: CommWrapper_MotorPorts/TestMotorOnPort:cancel End */
}

AsyncOperationState_t CommWrapper_MotorPorts_Async_SetPortConfig_Call(uint8_t port_idx, ByteArray_t configuration)
{
    /* Begin User Code Section: CommWrapper_MotorPorts/SetPortConfig:async_call Start */

    /* End User Code Section: CommWrapper_MotorPorts/SetPortConfig:async_call Start */
    AsyncOperationState_t returned_state = AsyncOperationState_Busy;
    MotorPortHandler_Configure_async_call_command = AsyncCommand_None;
    uint32_t primask = __get_PRIMASK();
    __disable_irq();
    if (MotorPortHandler_Configure_async_call_state == AsyncOperationState_Idle || MotorPortHandler_Configure_async_call_state == AsyncOperationState_Done)
    {
        MotorPortHandler_Configure_async_call_state = AsyncOperationState_Started;
        __set_PRIMASK(primask);

        MotorPortHandler_Configure_async_call_argument_port_idx = port_idx;
        MotorPortHandler_Configure_async_call_argument_configuration = configuration;

        returned_state = AsyncOperationState_Started;
        MotorPortHandler_Configure_async_call_command = AsyncCommand_Start;
    }
    else
    {
        __set_PRIMASK(primask);
    }
    return returned_state;
    /* Begin User Code Section: CommWrapper_MotorPorts/SetPortConfig:async_call End */

    /* End User Code Section: CommWrapper_MotorPorts/SetPortConfig:async_call End */
}

AsyncOperationState_t CommWrapper_MotorPorts_Async_SetPortConfig_GetResult(bool* result)
{
    /* Begin User Code Section: CommWrapper_MotorPorts/SetPortConfig:get_result Start */

    /* End User Code Section: CommWrapper_MotorPorts/SetPortConfig:get_result Start */
    AsyncOperationState_t returned_state;
    uint32_t primask = __get_PRIMASK();
    __disable_irq();
    switch (MotorPortHandler_Configure_async_call_state)
    {
        case AsyncOperationState_Done:
            if (result)
            {
                *result = MotorPortHandler_Configure_async_call_argument_result;
            }
            MotorPortHandler_Configure_async_call_state = AsyncOperationState_Idle;
            __set_PRIMASK(primask);
            returned_state = AsyncOperationState_Done;
            break;

        case AsyncOperationState_Started:
            __set_PRIMASK(primask);
            returned_state = AsyncOperationState_Busy;
            break;

        default:
            __set_PRIMASK(primask);
            returned_state = MotorPortHandler_Configure_async_call_state;
            break;
    }
    return returned_state;
    /* Begin User Code Section: CommWrapper_MotorPorts/SetPortConfig:get_result End */

    /* End User Code Section: CommWrapper_MotorPorts/SetPortConfig:get_result End */
}

void CommWrapper_MotorPorts_Async_SetPortConfig_Cancel(void)
{
    /* Begin User Code Section: CommWrapper_MotorPorts/SetPortConfig:cancel Start */

    /* End User Code Section: CommWrapper_MotorPorts/SetPortConfig:cancel Start */
    MotorPortHandler_Configure_async_call_command = AsyncCommand_Cancel;
    /* Begin User Code Section: CommWrapper_MotorPorts/SetPortConfig:cancel End */

    /* End User Code Section: CommWrapper_MotorPorts/SetPortConfig:cancel End */
}

void MasterCommunicationInterface_RaiseEvent_OnTransmissionComplete(void)
{
    /* Begin User Code Section: MasterCommunicationInterface/OnTransmissionComplete:run Start */

    /* End User Code Section: MasterCommunicationInterface/OnTransmissionComplete:run Start */
    RestartManager_RebootToBootloader_async_call_Update();
    /* Begin User Code Section: MasterCommunicationInterface/OnTransmissionComplete:run End */

    /* End User Code Section: MasterCommunicationInterface/OnTransmissionComplete:run End */
}

AsyncOperationState_t CommWrapper_Bootloader_Async_RebootToBootloader_Call(void)
{
    /* Begin User Code Section: CommWrapper_Bootloader/RebootToBootloader:async_call Start */

    /* End User Code Section: CommWrapper_Bootloader/RebootToBootloader:async_call Start */
    AsyncOperationState_t returned_state = AsyncOperationState_Busy;
    RestartManager_RebootToBootloader_async_call_command = AsyncCommand_None;
    uint32_t primask = __get_PRIMASK();
    __disable_irq();
    if (RestartManager_RebootToBootloader_async_call_state == AsyncOperationState_Idle || RestartManager_RebootToBootloader_async_call_state == AsyncOperationState_Done)
    {
        RestartManager_RebootToBootloader_async_call_state = AsyncOperationState_Started;
        __set_PRIMASK(primask);


        returned_state = AsyncOperationState_Started;
        RestartManager_RebootToBootloader_async_call_command = AsyncCommand_Start;
    }
    else
    {
        __set_PRIMASK(primask);
    }
    return returned_state;
    /* Begin User Code Section: CommWrapper_Bootloader/RebootToBootloader:async_call End */

    /* End User Code Section: CommWrapper_Bootloader/RebootToBootloader:async_call End */
}

AsyncOperationState_t CommWrapper_Bootloader_Async_RebootToBootloader_GetResult(void)
{
    /* Begin User Code Section: CommWrapper_Bootloader/RebootToBootloader:get_result Start */

    /* End User Code Section: CommWrapper_Bootloader/RebootToBootloader:get_result Start */
    AsyncOperationState_t returned_state;
    uint32_t primask = __get_PRIMASK();
    __disable_irq();
    switch (RestartManager_RebootToBootloader_async_call_state)
    {
        case AsyncOperationState_Done:
            RestartManager_RebootToBootloader_async_call_state = AsyncOperationState_Idle;
            __set_PRIMASK(primask);
            returned_state = AsyncOperationState_Done;
            break;

        case AsyncOperationState_Started:
            __set_PRIMASK(primask);
            returned_state = AsyncOperationState_Busy;
            break;

        default:
            __set_PRIMASK(primask);
            returned_state = RestartManager_RebootToBootloader_async_call_state;
            break;
    }
    return returned_state;
    /* Begin User Code Section: CommWrapper_Bootloader/RebootToBootloader:get_result End */

    /* End User Code Section: CommWrapper_Bootloader/RebootToBootloader:get_result End */
}

void CommWrapper_Bootloader_Async_RebootToBootloader_Cancel(void)
{
    /* Begin User Code Section: CommWrapper_Bootloader/RebootToBootloader:cancel Start */

    /* End User Code Section: CommWrapper_Bootloader/RebootToBootloader:cancel Start */
    RestartManager_RebootToBootloader_async_call_command = AsyncCommand_Cancel;
    /* Begin User Code Section: CommWrapper_Bootloader/RebootToBootloader:cancel End */

    /* End User Code Section: CommWrapper_Bootloader/RebootToBootloader:cancel End */
}

void ADC_RaiseEvent_InitDoneISR(void)
{
    /* Begin User Code Section: ADC/InitDoneISR:run Start */

    /* End User Code Section: ADC/InitDoneISR:run Start */
    MotorDriver_8833_Run_StartISR();
    /* Begin User Code Section: ADC/InitDoneISR:run End */

    /* End User Code Section: ADC/InitDoneISR:run End */
}

uint8_t MasterCommunication_Call_Calculate_CRC7(uint8_t init_value, ConstByteArray_t data)
{
    /* Begin User Code Section: MasterCommunication/Calculate_CRC7:run Start */

    /* End User Code Section: MasterCommunication/Calculate_CRC7:run Start */
    return CRC_Run_Calculate_CRC7(init_value, data);
    /* Begin User Code Section: MasterCommunication/Calculate_CRC7:run End */

    /* End User Code Section: MasterCommunication/Calculate_CRC7:run End */
}

uint16_t MasterCommunication_Call_Calculate_CRC16(uint16_t init_value, ConstByteArray_t data)
{
    /* Begin User Code Section: MasterCommunication/Calculate_CRC16:run Start */

    /* End User Code Section: MasterCommunication/Calculate_CRC16:run Start */
    return CRC_Run_Calculate_CRC16(init_value, data);
    /* Begin User Code Section: MasterCommunication/Calculate_CRC16:run End */

    /* End User Code Section: MasterCommunication/Calculate_CRC16:run End */
}

void* SensorPortHandler_Call_Allocate(size_t size)
{
    /* Begin User Code Section: SensorPortHandler/Allocate:run Start */

    /* End User Code Section: SensorPortHandler/Allocate:run Start */
    return MemoryAllocator_Run_Allocate(size);
    /* Begin User Code Section: SensorPortHandler/Allocate:run End */

    /* End User Code Section: SensorPortHandler/Allocate:run End */
}

void* MotorPortHandler_Call_Allocate(size_t size)
{
    /* Begin User Code Section: MotorPortHandler/Allocate:run Start */

    /* End User Code Section: MotorPortHandler/Allocate:run Start */
    return MemoryAllocator_Run_Allocate(size);
    /* Begin User Code Section: MotorPortHandler/Allocate:run End */

    /* End User Code Section: MotorPortHandler/Allocate:run End */
}

void SensorPortHandler_Call_Free(void** ptr)
{
    /* Begin User Code Section: SensorPortHandler/Free:run Start */

    /* End User Code Section: SensorPortHandler/Free:run Start */
    MemoryAllocator_Run_Free(ptr);
    /* Begin User Code Section: SensorPortHandler/Free:run End */

    /* End User Code Section: SensorPortHandler/Free:run End */
}

void MotorPortHandler_Call_Free(void** ptr)
{
    /* Begin User Code Section: MotorPortHandler/Free:run Start */

    /* End User Code Section: MotorPortHandler/Free:run Start */
    MemoryAllocator_Run_Free(ptr);
    /* Begin User Code Section: MotorPortHandler/Free:run End */

    /* End User Code Section: MotorPortHandler/Free:run End */
}

void IMU_Call_LogError(const ErrorInfo_t* data)
{
    /* Begin User Code Section: IMU/LogError:run Start */

    /* End User Code Section: IMU/LogError:run Start */
    ErrorStorage_Run_Store(data);
    /* Begin User Code Section: IMU/LogError:run End */

    /* End User Code Section: IMU/LogError:run End */
}

void MasterCommunicationInterface_Call_LogError(const ErrorInfo_t* data)
{
    /* Begin User Code Section: MasterCommunicationInterface/LogError:run Start */

    /* End User Code Section: MasterCommunicationInterface/LogError:run Start */
    ErrorStorage_Run_Store(data);
    /* Begin User Code Section: MasterCommunicationInterface/LogError:run End */

    /* End User Code Section: MasterCommunicationInterface/LogError:run End */
}

void CommWrapper_ErrorStorage_Call_ClearMemory(void)
{
    /* Begin User Code Section: CommWrapper_ErrorStorage/ClearMemory:run Start */

    /* End User Code Section: CommWrapper_ErrorStorage/ClearMemory:run Start */
    ErrorStorage_Run_Clear();
    /* Begin User Code Section: CommWrapper_ErrorStorage/ClearMemory:run End */

    /* End User Code Section: CommWrapper_ErrorStorage/ClearMemory:run End */
}

bool CommWrapper_ErrorStorage_Call_Read(uint32_t index, ErrorInfo_t* error)
{
    (void) error;
    /* Begin User Code Section: CommWrapper_ErrorStorage/Read:run Start */

    /* End User Code Section: CommWrapper_ErrorStorage/Read:run Start */
    return ErrorStorage_Run_Read(index, error);
    /* Begin User Code Section: CommWrapper_ErrorStorage/Read:run End */

    /* End User Code Section: CommWrapper_ErrorStorage/Read:run End */
}

void CommWrapper_ErrorStorage_Call_Store(const ErrorInfo_t* error)
{
    (void) error;
    /* Begin User Code Section: CommWrapper_ErrorStorage/Store:run Start */

    /* End User Code Section: CommWrapper_ErrorStorage/Store:run Start */
    ErrorStorage_Run_Store(error);
    /* Begin User Code Section: CommWrapper_ErrorStorage/Store:run End */

    /* End User Code Section: CommWrapper_ErrorStorage/Store:run End */
}

void MasterCommunication_Call_SendResponse(ConstByteArray_t response)
{
    /* Begin User Code Section: MasterCommunication/SendResponse:run Start */

    /* End User Code Section: MasterCommunication/SendResponse:run Start */
    MasterCommunicationInterface_Run_SetResponse(response);
    /* Begin User Code Section: MasterCommunication/SendResponse:run End */

    /* End User Code Section: MasterCommunication/SendResponse:run End */
}

uint32_t SensorPortHandler_Call_ReadCurrentTicks(void)
{
    /* Begin User Code Section: SensorPortHandler/ReadCurrentTicks:run Start */

    /* End User Code Section: SensorPortHandler/ReadCurrentTicks:run Start */
    return HighResolutionTimer_Run_GetTickCount();
    /* Begin User Code Section: SensorPortHandler/ReadCurrentTicks:run End */

    /* End User Code Section: SensorPortHandler/ReadCurrentTicks:run End */
}

float SensorPortHandler_Call_ConvertTicksToMs(uint32_t ticks)
{
    /* Begin User Code Section: SensorPortHandler/ConvertTicksToMs:run Start */

    /* End User Code Section: SensorPortHandler/ConvertTicksToMs:run Start */
    return HighResolutionTimer_Run_ToMs(ticks);
    /* Begin User Code Section: SensorPortHandler/ConvertTicksToMs:run End */

    /* End User Code Section: SensorPortHandler/ConvertTicksToMs:run End */
}

void CommWrapper_McuStatusCollector_Call_ResetSlots(void)
{
    /* Begin User Code Section: CommWrapper_McuStatusCollector/ResetSlots:run Start */

    /* End User Code Section: CommWrapper_McuStatusCollector/ResetSlots:run Start */
    McuStatusCollector_Run_Reset();
    /* Begin User Code Section: CommWrapper_McuStatusCollector/ResetSlots:run End */

    /* End User Code Section: CommWrapper_McuStatusCollector/ResetSlots:run End */
}

void CommWrapper_McuStatusCollector_Call_EnableSlot(uint8_t slot)
{
    /* Begin User Code Section: CommWrapper_McuStatusCollector/EnableSlot:run Start */

    /* End User Code Section: CommWrapper_McuStatusCollector/EnableSlot:run Start */
    McuStatusCollector_Run_EnableSlot(slot);
    ConfigEventProvider_Run_DispatchConfigEvent();
    /* Begin User Code Section: CommWrapper_McuStatusCollector/EnableSlot:run End */

    /* End User Code Section: CommWrapper_McuStatusCollector/EnableSlot:run End */
}

void CommWrapper_McuStatusCollector_Call_DisableSlot(uint8_t slot)
{
    /* Begin User Code Section: CommWrapper_McuStatusCollector/DisableSlot:run Start */

    /* End User Code Section: CommWrapper_McuStatusCollector/DisableSlot:run Start */
    McuStatusCollector_Run_DisableSlot(slot);
    /* Begin User Code Section: CommWrapper_McuStatusCollector/DisableSlot:run End */

    /* End User Code Section: CommWrapper_McuStatusCollector/DisableSlot:run End */
}

uint8_t CommWrapper_McuStatusCollector_Call_Read(ByteArray_t destination)
{
    /* Begin User Code Section: CommWrapper_McuStatusCollector/Read:run Start */

    /* End User Code Section: CommWrapper_McuStatusCollector/Read:run Start */
    return McuStatusCollector_Run_Read(destination);
    /* Begin User Code Section: CommWrapper_McuStatusCollector/Read:run End */

    /* End User Code Section: CommWrapper_McuStatusCollector/Read:run End */
}

void MotorPortHandler_Call_UpdatePortStatus(uint8_t port, ByteArray_t data)
{
    /* Begin User Code Section: MotorPortHandler/UpdatePortStatus:run Start */

    /* End User Code Section: MotorPortHandler/UpdatePortStatus:run Start */
    McuStatusSlots_Run_UpdateMotorPort(port, data);
    /* Begin User Code Section: MotorPortHandler/UpdatePortStatus:run End */

    /* End User Code Section: MotorPortHandler/UpdatePortStatus:run End */
}

void SensorPortHandler_Call_UpdatePortStatus(uint8_t port, ByteArray_t data)
{
    /* Begin User Code Section: SensorPortHandler/UpdatePortStatus:run Start */

    /* End User Code Section: SensorPortHandler/UpdatePortStatus:run Start */
    McuStatusSlots_Run_UpdateSensorPort(port, data);
    /* Begin User Code Section: SensorPortHandler/UpdatePortStatus:run End */

    /* End User Code Section: SensorPortHandler/UpdatePortStatus:run End */
}

ssize_t CommWrapper_LedDisplay_Call_ReadScenarioName(RingLedScenario_t scenario, ByteArray_t destination)
{
    /* Begin User Code Section: CommWrapper_LedDisplay/ReadScenarioName:run Start */

    /* End User Code Section: CommWrapper_LedDisplay/ReadScenarioName:run Start */
    return RingLedDisplay_Run_ReadScenarioName(scenario, destination);
    /* Begin User Code Section: CommWrapper_LedDisplay/ReadScenarioName:run End */

    /* End User Code Section: CommWrapper_LedDisplay/ReadScenarioName:run End */
}

void CommWrapper_SensorPorts_Call_ReadPortTypes(ByteArray_t* buffer)
{
    /* Begin User Code Section: CommWrapper_SensorPorts/ReadPortTypes:run Start */

    /* End User Code Section: CommWrapper_SensorPorts/ReadPortTypes:run Start */
    SensorPortHandler_Run_ReadPortTypes(buffer);
    /* Begin User Code Section: CommWrapper_SensorPorts/ReadPortTypes:run End */

    /* End User Code Section: CommWrapper_SensorPorts/ReadPortTypes:run End */
}

void CommWrapper_SensorPorts_Call_ReadSensorInfo(uint8_t port_idx, uint8_t page, ByteArray_t* buffer)
{
    /* Begin User Code Section: CommWrapper_SensorPorts/ReadSensorInfo:run Start */

    /* End User Code Section: CommWrapper_SensorPorts/ReadSensorInfo:run Start */
    SensorPortHandler_Run_ReadSensorInfo(port_idx, page, buffer);
    /* Begin User Code Section: CommWrapper_SensorPorts/ReadSensorInfo:run End */

    /* End User Code Section: CommWrapper_SensorPorts/ReadSensorInfo:run End */
}

void CommWrapper_MotorPorts_Call_ReadPortTypes(ByteArray_t* buffer)
{
    /* Begin User Code Section: CommWrapper_MotorPorts/ReadPortTypes:run Start */

    /* End User Code Section: CommWrapper_MotorPorts/ReadPortTypes:run Start */
    MotorPortHandler_Run_ReadPortTypes(buffer);
    /* Begin User Code Section: CommWrapper_MotorPorts/ReadPortTypes:run End */

    /* End User Code Section: CommWrapper_MotorPorts/ReadPortTypes:run End */
}

bool CommWrapper_MotorPorts_Call_CreateDriveRequest(uint8_t port_idx, ConstByteArray_t buffer, DriveRequest_t* request)
{
    /* Begin User Code Section: CommWrapper_MotorPorts/CreateDriveRequest:run Start */

    /* End User Code Section: CommWrapper_MotorPorts/CreateDriveRequest:run Start */
    return MotorPortHandler_Run_CreateDriveRequest(port_idx, buffer, request);
    /* Begin User Code Section: CommWrapper_MotorPorts/CreateDriveRequest:run End */

    /* End User Code Section: CommWrapper_MotorPorts/CreateDriveRequest:run End */
}

void ADC_Write_MainBatteryVoltage(Voltage_t value)
{
    /* Begin User Code Section: ADC/MainBatteryVoltage:write Start */

    /* End User Code Section: ADC/MainBatteryVoltage:write Start */
    ADC_MainBatteryVoltage_variable = value;
    /* Begin User Code Section: ADC/MainBatteryVoltage:write End */

    /* End User Code Section: ADC/MainBatteryVoltage:write End */
}

void ADC_Write_MotorBatteryVoltage(Voltage_t value)
{
    /* Begin User Code Section: ADC/MotorBatteryVoltage:write Start */

    /* End User Code Section: ADC/MotorBatteryVoltage:write Start */
    ADC_MotorBatteryVoltage_variable = value;
    /* Begin User Code Section: ADC/MotorBatteryVoltage:write End */

    /* End User Code Section: ADC/MotorBatteryVoltage:write End */
}

void ADC_Write_MotorCurrent(uint32_t index, Current_t value)
{
    ASSERT(index < 6);
    /* Begin User Code Section: ADC/MotorCurrent:write Start */

    /* End User Code Section: ADC/MotorCurrent:write Start */
    ADC_MotorCurrent_array[index] = value;
    /* Begin User Code Section: ADC/MotorCurrent:write End */

    /* End User Code Section: ADC/MotorCurrent:write End */
}

void ADC_Write_Sensor_ADC(uint32_t index, uint8_t value)
{
    ASSERT(index < 4);
    /* Begin User Code Section: ADC/Sensor_ADC:write Start */

    /* End User Code Section: ADC/Sensor_ADC:write Start */
    ADC_Sensor_ADC_array[index] = value;
    /* Begin User Code Section: ADC/Sensor_ADC:write End */

    /* End User Code Section: ADC/Sensor_ADC:write End */
}

void BatteryCalculator_Write_MainBatteryLevel(uint8_t value)
{
    /* Begin User Code Section: BatteryCalculator/MainBatteryLevel:write Start */

    /* End User Code Section: BatteryCalculator/MainBatteryLevel:write Start */
    BatteryCalculator_MainBatteryLevel_variable = value;
    /* Begin User Code Section: BatteryCalculator/MainBatteryLevel:write End */

    /* End User Code Section: BatteryCalculator/MainBatteryLevel:write End */
}

void BatteryCalculator_Write_MainBatteryLow(bool value)
{
    /* Begin User Code Section: BatteryCalculator/MainBatteryLow:write Start */

    /* End User Code Section: BatteryCalculator/MainBatteryLow:write Start */
    BatteryCalculator_MainBatteryLow_variable = value;
    /* Begin User Code Section: BatteryCalculator/MainBatteryLow:write End */

    /* End User Code Section: BatteryCalculator/MainBatteryLow:write End */
}

void BatteryCalculator_Write_MotorBatteryLevel(uint8_t value)
{
    /* Begin User Code Section: BatteryCalculator/MotorBatteryLevel:write Start */

    /* End User Code Section: BatteryCalculator/MotorBatteryLevel:write Start */
    BatteryCalculator_MotorBatteryLevel_variable = value;
    /* Begin User Code Section: BatteryCalculator/MotorBatteryLevel:write End */

    /* End User Code Section: BatteryCalculator/MotorBatteryLevel:write End */
}

void BatteryCalculator_Write_MotorBatteryPresent(bool value)
{
    /* Begin User Code Section: BatteryCalculator/MotorBatteryPresent:write Start */

    /* End User Code Section: BatteryCalculator/MotorBatteryPresent:write Start */
    BatteryCalculator_MotorBatteryPresent_variable = value;
    BatteryCalculator_MotorBatteryPresent_variable1 = value;
    /* Begin User Code Section: BatteryCalculator/MotorBatteryPresent:write End */

    /* End User Code Section: BatteryCalculator/MotorBatteryPresent:write End */
}

void BatteryCharger_Write_ChargerState(ChargerState_t value)
{
    /* Begin User Code Section: BatteryCharger/ChargerState:write Start */

    /* End User Code Section: BatteryCharger/ChargerState:write Start */
    BatteryCharger_ChargerState_variable = value;
    /* Begin User Code Section: BatteryCharger/ChargerState:write End */

    /* End User Code Section: BatteryCharger/ChargerState:write End */
}

void BluetoothStatusObserver_Write_ConnectionStatus(BluetoothStatus_t value)
{
    /* Begin User Code Section: BluetoothStatusObserver/ConnectionStatus:write Start */

    /* End User Code Section: BluetoothStatusObserver/ConnectionStatus:write Start */
    BluetoothStatusObserver_ConnectionStatus_variable = value;
    /* Begin User Code Section: BluetoothStatusObserver/ConnectionStatus:write End */

    /* End User Code Section: BluetoothStatusObserver/ConnectionStatus:write End */
}

void CommWrapper_LedDisplay_Write_Scenario(RingLedScenario_t value)
{
    /* Begin User Code Section: CommWrapper_LedDisplay/Scenario:write Start */

    /* End User Code Section: CommWrapper_LedDisplay/Scenario:write Start */
    CommWrapper_LedDisplay_Scenario_variable = value;
    /* Begin User Code Section: CommWrapper_LedDisplay/Scenario:write End */

    /* End User Code Section: CommWrapper_LedDisplay/Scenario:write End */
}

void CommWrapper_LedDisplay_Write_UserFrame(uint32_t index, rgb_t value)
{
    ASSERT(index < 12);
    /* Begin User Code Section: CommWrapper_LedDisplay/UserFrame:write Start */

    /* End User Code Section: CommWrapper_LedDisplay/UserFrame:write Start */
    CommWrapper_LedDisplay_UserFrame_array[index] = value;
    /* Begin User Code Section: CommWrapper_LedDisplay/UserFrame:write End */

    /* End User Code Section: CommWrapper_LedDisplay/UserFrame:write End */
}

void CommWrapper_MotorPorts_Write_DriveRequest(uint32_t index, const DriveRequest_t* value)
{
    ASSERT(index < 6);
    ASSERT(value != NULL);
    /* Begin User Code Section: CommWrapper_MotorPorts/DriveRequest:write Start */

    /* End User Code Section: CommWrapper_MotorPorts/DriveRequest:write Start */
    CommWrapper_MotorPorts_DriveRequest_array[index] = *value;
    /* Begin User Code Section: CommWrapper_MotorPorts/DriveRequest:write End */

    /* End User Code Section: CommWrapper_MotorPorts/DriveRequest:write End */
}

void ErrorStorage_Write_NumberOfStoredErrors(uint32_t value)
{
    /* Begin User Code Section: ErrorStorage/NumberOfStoredErrors:write Start */

    /* End User Code Section: ErrorStorage/NumberOfStoredErrors:write Start */
    ErrorStorage_NumberOfStoredErrors_variable = value;
    /* Begin User Code Section: ErrorStorage/NumberOfStoredErrors:write End */

    /* End User Code Section: ErrorStorage/NumberOfStoredErrors:write End */
}

void GyroscopeOffsetCompensator_Write_CompensatedAngularSpeeds(const Vector3D_t* value)
{
    ASSERT(value != NULL);
    /* Begin User Code Section: GyroscopeOffsetCompensator/CompensatedAngularSpeeds:write Start */

    /* End User Code Section: GyroscopeOffsetCompensator/CompensatedAngularSpeeds:write Start */
    if (GyroscopeOffsetCompensator_CompensatedAngularSpeeds_queue_count < 32u)
    {
        ++GyroscopeOffsetCompensator_CompensatedAngularSpeeds_queue_count;
    }
    else
    {
        GyroscopeOffsetCompensator_CompensatedAngularSpeeds_queue_overflow = true;
    }
    size_t GyroscopeOffsetCompensator_CompensatedAngularSpeeds_queue_idx = GyroscopeOffsetCompensator_CompensatedAngularSpeeds_queue_write_index;
    GyroscopeOffsetCompensator_CompensatedAngularSpeeds_queue_write_index = (GyroscopeOffsetCompensator_CompensatedAngularSpeeds_queue_write_index + 1u) % 32u;
    GyroscopeOffsetCompensator_CompensatedAngularSpeeds_queue[GyroscopeOffsetCompensator_CompensatedAngularSpeeds_queue_idx] = *value;
    /* Begin User Code Section: GyroscopeOffsetCompensator/CompensatedAngularSpeeds:write End */

    /* End User Code Section: GyroscopeOffsetCompensator/CompensatedAngularSpeeds:write End */
}

void IMU_Write_AccelerometerSample(const Vector3D_t* value)
{
    ASSERT(value != NULL);
    /* Begin User Code Section: IMU/AccelerometerSample:write Start */

    /* End User Code Section: IMU/AccelerometerSample:write Start */
    if (IMU_AccelerometerSample_queue_count < 32u)
    {
        ++IMU_AccelerometerSample_queue_count;
    }
    else
    {
        IMU_AccelerometerSample_queue_overflow = true;
    }
    size_t IMU_AccelerometerSample_queue_idx = IMU_AccelerometerSample_queue_write_index;
    IMU_AccelerometerSample_queue_write_index = (IMU_AccelerometerSample_queue_write_index + 1u) % 32u;
    IMU_AccelerometerSample_queue[IMU_AccelerometerSample_queue_idx] = *value;
    /* Begin User Code Section: IMU/AccelerometerSample:write End */

    /* End User Code Section: IMU/AccelerometerSample:write End */
}

void IMU_Write_GyroscopeSample(const Vector3D_t* value)
{
    ASSERT(value != NULL);
    /* Begin User Code Section: IMU/GyroscopeSample:write Start */

    /* End User Code Section: IMU/GyroscopeSample:write Start */
    if (IMU_GyroscopeSample_queue_count < 8u)
    {
        ++IMU_GyroscopeSample_queue_count;
    }
    else
    {
        IMU_GyroscopeSample_queue_overflow = true;
    }
    size_t IMU_GyroscopeSample_queue_idx = IMU_GyroscopeSample_queue_write_index;
    IMU_GyroscopeSample_queue_write_index = (IMU_GyroscopeSample_queue_write_index + 1u) % 8u;
    IMU_GyroscopeSample_queue[IMU_GyroscopeSample_queue_idx] = *value;
    if (IMU_GyroscopeSample_queue1_count < 8u)
    {
        ++IMU_GyroscopeSample_queue1_count;
    }
    else
    {
        IMU_GyroscopeSample_queue1_overflow = true;
    }
    size_t IMU_GyroscopeSample_queue1_idx = IMU_GyroscopeSample_queue1_write_index;
    IMU_GyroscopeSample_queue1_write_index = (IMU_GyroscopeSample_queue1_write_index + 1u) % 8u;
    IMU_GyroscopeSample_queue1[IMU_GyroscopeSample_queue1_idx] = *value;
    /* Begin User Code Section: IMU/GyroscopeSample:write End */

    /* End User Code Section: IMU/GyroscopeSample:write End */
}

void IMU_Write_RawAccelerometerSample(const IMU_RawSample_t* value)
{
    ASSERT(value != NULL);
    /* Begin User Code Section: IMU/RawAccelerometerSample:write Start */

    /* End User Code Section: IMU/RawAccelerometerSample:write Start */
    IMU_RawAccelerometerSample_variable = *value;
    /* Begin User Code Section: IMU/RawAccelerometerSample:write End */

    /* End User Code Section: IMU/RawAccelerometerSample:write End */
}

void IMU_Write_RawGyroscopeSample(const IMU_RawSample_t* value)
{
    ASSERT(value != NULL);
    /* Begin User Code Section: IMU/RawGyroscopeSample:write Start */

    /* End User Code Section: IMU/RawGyroscopeSample:write Start */
    IMU_RawGyroscopeSample_variable = *value;
    /* Begin User Code Section: IMU/RawGyroscopeSample:write End */

    /* End User Code Section: IMU/RawGyroscopeSample:write End */
}

void IMUMovementDetector_Write_IsMoving(bool value)
{
    /* Begin User Code Section: IMUMovementDetector/IsMoving:write Start */

    /* End User Code Section: IMUMovementDetector/IsMoving:write Start */
    IMUMovementDetector_IsMoving_variable = value;
    /* Begin User Code Section: IMUMovementDetector/IsMoving:write End */

    /* End User Code Section: IMUMovementDetector/IsMoving:write End */
}

void IMUOrientationEstimator_Write_OrientationEulerDegrees(const Orientation3D_t* value)
{
    ASSERT(value != NULL);
    /* Begin User Code Section: IMUOrientationEstimator/OrientationEulerDegrees:write Start */

    /* End User Code Section: IMUOrientationEstimator/OrientationEulerDegrees:write Start */
    IMUOrientationEstimator_OrientationEulerDegrees_variable = *value;
    IMUOrientationEstimator_OrientationEulerDegrees_variable1 = *value;
    /* Begin User Code Section: IMUOrientationEstimator/OrientationEulerDegrees:write End */

    /* End User Code Section: IMUOrientationEstimator/OrientationEulerDegrees:write End */
}

void LedDisplayController_Write_Leds(uint32_t index, rgb_t value)
{
    ASSERT(index < 16);
    /* Begin User Code Section: LedDisplayController/Leds:write Start */

    /* End User Code Section: LedDisplayController/Leds:write Start */
    LedDisplayController_Leds_array[index] = value;
    /* Begin User Code Section: LedDisplayController/Leds:write End */

    /* End User Code Section: LedDisplayController/Leds:write End */
}

void LedDisplayController_Write_MaxBrightness(uint8_t value)
{
    /* Begin User Code Section: LedDisplayController/MaxBrightness:write Start */

    /* End User Code Section: LedDisplayController/MaxBrightness:write Start */
    LedDisplayController_MaxBrightness_variable = value;
    /* Begin User Code Section: LedDisplayController/MaxBrightness:write End */

    /* End User Code Section: LedDisplayController/MaxBrightness:write End */
}

void MasterStatusObserver_Write_EnableCommunicationObserver(bool value)
{
    /* Begin User Code Section: MasterStatusObserver/EnableCommunicationObserver:write Start */

    /* End User Code Section: MasterStatusObserver/EnableCommunicationObserver:write Start */
    MasterStatusObserver_EnableCommunicationObserver_variable = value;
    /* Begin User Code Section: MasterStatusObserver/EnableCommunicationObserver:write End */

    /* End User Code Section: MasterStatusObserver/EnableCommunicationObserver:write End */
}

void MasterStatusObserver_Write_MasterStatus(MasterStatus_t value)
{
    /* Begin User Code Section: MasterStatusObserver/MasterStatus:write Start */

    /* End User Code Section: MasterStatusObserver/MasterStatus:write Start */
    MasterStatusObserver_MasterStatus_variable = value;
    /* Begin User Code Section: MasterStatusObserver/MasterStatus:write End */

    /* End User Code Section: MasterStatusObserver/MasterStatus:write End */
}

void McuStatusSlots_Write_SlotData(uint32_t index, SlotData_t value)
{
    ASSERT(index < 16);
    /* Begin User Code Section: McuStatusSlots/SlotData:write Start */

    /* End User Code Section: McuStatusSlots/SlotData:write Start */
    McuStatusSlots_SlotData_array[index] = value;
    /* Begin User Code Section: McuStatusSlots/SlotData:write End */

    /* End User Code Section: McuStatusSlots/SlotData:write End */
}

void MotorCurrentFilter_Write_FilteredCurrent(uint32_t index, Current_t value)
{
    ASSERT(index < 6);
    /* Begin User Code Section: MotorCurrentFilter/FilteredCurrent:write Start */

    /* End User Code Section: MotorCurrentFilter/FilteredCurrent:write Start */
    MotorCurrentFilter_FilteredCurrent_array[index] = value;
    /* Begin User Code Section: MotorCurrentFilter/FilteredCurrent:write End */

    /* End User Code Section: MotorCurrentFilter/FilteredCurrent:write End */
}

void MotorDerating_Write_MaxPowerRatio(uint32_t index, Percentage_t value)
{
    (void) value;
    ASSERT(index < 6);
    /* Begin User Code Section: MotorDerating/MaxPowerRatio:write Start */

    /* End User Code Section: MotorDerating/MaxPowerRatio:write Start */
    /* Begin User Code Section: MotorDerating/MaxPowerRatio:write End */

    /* End User Code Section: MotorDerating/MaxPowerRatio:write End */
}

void MotorDerating_Write_RelativeMotorCurrent(uint32_t index, Percentage_t value)
{
    ASSERT(index < 6);
    /* Begin User Code Section: MotorDerating/RelativeMotorCurrent:write Start */

    /* End User Code Section: MotorDerating/RelativeMotorCurrent:write Start */
    MotorDerating_RelativeMotorCurrent_array[index] = value;
    /* Begin User Code Section: MotorDerating/RelativeMotorCurrent:write End */

    /* End User Code Section: MotorDerating/RelativeMotorCurrent:write End */
}

void MotorPortHandler_Write_DriveStrength(uint32_t index, int16_t value)
{
    ASSERT(index < 6);
    /* Begin User Code Section: MotorPortHandler/DriveStrength:write Start */

    /* End User Code Section: MotorPortHandler/DriveStrength:write Start */
    MotorPortHandler_DriveStrength_array[index] = value;
    /* Begin User Code Section: MotorPortHandler/DriveStrength:write End */

    /* End User Code Section: MotorPortHandler/DriveStrength:write End */
}

void MotorPortHandler_Write_MaxAllowedCurrent(uint32_t index, Current_t value)
{
    ASSERT(index < 6);
    /* Begin User Code Section: MotorPortHandler/MaxAllowedCurrent:write Start */

    /* End User Code Section: MotorPortHandler/MaxAllowedCurrent:write Start */
    MotorPortHandler_MaxAllowedCurrent_array[index] = value;
    /* Begin User Code Section: MotorPortHandler/MaxAllowedCurrent:write End */

    /* End User Code Section: MotorPortHandler/MaxAllowedCurrent:write End */
}

void MotorPortHandler_Write_PortCount(uint8_t value)
{
    /* Begin User Code Section: MotorPortHandler/PortCount:write Start */

    /* End User Code Section: MotorPortHandler/PortCount:write Start */
    MotorPortHandler_PortCount_variable = value;
    /* Begin User Code Section: MotorPortHandler/PortCount:write End */

    /* End User Code Section: MotorPortHandler/PortCount:write End */
}

void MotorThermalModel_Write_Temperature(uint32_t index, Temperature_t value)
{
    ASSERT(index < 6);
    /* Begin User Code Section: MotorThermalModel/Temperature:write Start */

    /* End User Code Section: MotorThermalModel/Temperature:write Start */
    MotorThermalModel_Temperature_array[index] = value;
    /* Begin User Code Section: MotorThermalModel/Temperature:write End */

    /* End User Code Section: MotorThermalModel/Temperature:write End */
}

void RingLedDisplay_Write_LedColor(uint32_t index, rgb_t value)
{
    ASSERT(index < 12);
    /* Begin User Code Section: RingLedDisplay/LedColor:write Start */

    /* End User Code Section: RingLedDisplay/LedColor:write Start */
    RingLedDisplay_LedColor_array[index] = value;
    /* Begin User Code Section: RingLedDisplay/LedColor:write End */

    /* End User Code Section: RingLedDisplay/LedColor:write End */
}

void StartupReasonProvider_Write_IsColdStart(bool value)
{
    /* Begin User Code Section: StartupReasonProvider/IsColdStart:write Start */

    /* End User Code Section: StartupReasonProvider/IsColdStart:write Start */
    StartupReasonProvider_IsColdStart_variable = value;
    /* Begin User Code Section: StartupReasonProvider/IsColdStart:write End */

    /* End User Code Section: StartupReasonProvider/IsColdStart:write End */
}

void BatteryCalculator_Read_MainBatteryParameters(BatteryConfiguration_t* value)
{
    ASSERT(value != NULL);
    /* Begin User Code Section: BatteryCalculator/MainBatteryParameters:read Start */

    /* End User Code Section: BatteryCalculator/MainBatteryParameters:read Start */
    ProjectConfiguration_Constant_MainBatteryParameters(value);
    /* Begin User Code Section: BatteryCalculator/MainBatteryParameters:read End */

    /* End User Code Section: BatteryCalculator/MainBatteryParameters:read End */
}

Voltage_t BatteryCalculator_Read_MainBatteryVoltage(void)
{
    /* Begin User Code Section: BatteryCalculator/MainBatteryVoltage:read Start */

    /* End User Code Section: BatteryCalculator/MainBatteryVoltage:read Start */
    return ADC_MainBatteryVoltage_variable;
    /* Begin User Code Section: BatteryCalculator/MainBatteryVoltage:read End */

    /* End User Code Section: BatteryCalculator/MainBatteryVoltage:read End */
}

void BatteryCalculator_Read_MotorBatteryParameters(BatteryConfiguration_t* value)
{
    ASSERT(value != NULL);
    /* Begin User Code Section: BatteryCalculator/MotorBatteryParameters:read Start */

    /* End User Code Section: BatteryCalculator/MotorBatteryParameters:read Start */
    ProjectConfiguration_Constant_MotorBatteryParameters(value);
    /* Begin User Code Section: BatteryCalculator/MotorBatteryParameters:read End */

    /* End User Code Section: BatteryCalculator/MotorBatteryParameters:read End */
}

Voltage_t BatteryCalculator_Read_MotorBatteryVoltage(void)
{
    /* Begin User Code Section: BatteryCalculator/MotorBatteryVoltage:read Start */

    /* End User Code Section: BatteryCalculator/MotorBatteryVoltage:read Start */
    return ADC_MotorBatteryVoltage_variable;
    /* Begin User Code Section: BatteryCalculator/MotorBatteryVoltage:read End */

    /* End User Code Section: BatteryCalculator/MotorBatteryVoltage:read End */
}

uint32_t CommWrapper_ErrorStorage_Read_NumberOfStoredErrors(void)
{
    /* Begin User Code Section: CommWrapper_ErrorStorage/NumberOfStoredErrors:read Start */

    /* End User Code Section: CommWrapper_ErrorStorage/NumberOfStoredErrors:read Start */
    return ErrorStorage_NumberOfStoredErrors_variable;
    /* Begin User Code Section: CommWrapper_ErrorStorage/NumberOfStoredErrors:read End */

    /* End User Code Section: CommWrapper_ErrorStorage/NumberOfStoredErrors:read End */
}

size_t CommWrapper_LedDisplay_Read_ScenarioCount(void)
{
    /* Begin User Code Section: CommWrapper_LedDisplay/ScenarioCount:read Start */

    /* End User Code Section: CommWrapper_LedDisplay/ScenarioCount:read Start */
    return RingLedDisplay_Constant_ScenarioCount();
    /* Begin User Code Section: CommWrapper_LedDisplay/ScenarioCount:read End */

    /* End User Code Section: CommWrapper_LedDisplay/ScenarioCount:read End */
}

uint8_t CommWrapper_MotorPorts_Read_PortCount(void)
{
    /* Begin User Code Section: CommWrapper_MotorPorts/PortCount:read Start */

    /* End User Code Section: CommWrapper_MotorPorts/PortCount:read Start */
    return MotorPortHandler_PortCount_variable;
    /* Begin User Code Section: CommWrapper_MotorPorts/PortCount:read End */

    /* End User Code Section: CommWrapper_MotorPorts/PortCount:read End */
}

uint8_t CommWrapper_SensorPorts_Read_PortCount(void)
{
    /* Begin User Code Section: CommWrapper_SensorPorts/PortCount:read Start */

    /* End User Code Section: CommWrapper_SensorPorts/PortCount:read Start */
    return SensorPortHandler_Constant_PortCount();
    /* Begin User Code Section: CommWrapper_SensorPorts/PortCount:read End */

    /* End User Code Section: CommWrapper_SensorPorts/PortCount:read End */
}

ByteArray_t CommWrapper_VersionProvider_Read_FirmwareVersionString(void)
{
    /* Begin User Code Section: CommWrapper_VersionProvider/FirmwareVersionString:read Start */

    /* End User Code Section: CommWrapper_VersionProvider/FirmwareVersionString:read Start */
    return VersionProvider_Constant_FirmwareVersionString();
    /* Begin User Code Section: CommWrapper_VersionProvider/FirmwareVersionString:read End */

    /* End User Code Section: CommWrapper_VersionProvider/FirmwareVersionString:read End */
}

uint32_t CommWrapper_VersionProvider_Read_HardwareVersion(void)
{
    /* Begin User Code Section: CommWrapper_VersionProvider/HardwareVersion:read Start */

    /* End User Code Section: CommWrapper_VersionProvider/HardwareVersion:read Start */
    return VersionProvider_Constant_HardwareVersion();
    /* Begin User Code Section: CommWrapper_VersionProvider/HardwareVersion:read End */

    /* End User Code Section: CommWrapper_VersionProvider/HardwareVersion:read End */
}

bool CommunicationObserver_Read_IsEnabled(void)
{
    /* Begin User Code Section: CommunicationObserver/IsEnabled:read Start */

    /* End User Code Section: CommunicationObserver/IsEnabled:read Start */
    return MasterStatusObserver_EnableCommunicationObserver_variable;
    /* Begin User Code Section: CommunicationObserver/IsEnabled:read End */

    /* End User Code Section: CommunicationObserver/IsEnabled:read End */
}

uint32_t ErrorStorage_Read_FirmwareVersion(void)
{
    /* Begin User Code Section: ErrorStorage/FirmwareVersion:read Start */

    /* End User Code Section: ErrorStorage/FirmwareVersion:read Start */
    return VersionProvider_Constant_FirmwareVersion();
    /* Begin User Code Section: ErrorStorage/FirmwareVersion:read End */

    /* End User Code Section: ErrorStorage/FirmwareVersion:read End */
}

uint32_t ErrorStorage_Read_HardwareVersion(void)
{
    /* Begin User Code Section: ErrorStorage/HardwareVersion:read Start */

    /* End User Code Section: ErrorStorage/HardwareVersion:read Start */
    return VersionProvider_Constant_HardwareVersion();
    /* Begin User Code Section: ErrorStorage/HardwareVersion:read End */

    /* End User Code Section: ErrorStorage/HardwareVersion:read End */
}

QueueStatus_t GyroscopeOffsetCompensator_Read_AngularSpeeds(Vector3D_t* value)
{
    ASSERT(value != NULL);
    /* Begin User Code Section: GyroscopeOffsetCompensator/AngularSpeeds:read Start */

    /* End User Code Section: GyroscopeOffsetCompensator/AngularSpeeds:read Start */
    if (IMU_GyroscopeSample_queue_count > 0u)
    {
        size_t idx = (IMU_GyroscopeSample_queue_write_index - IMU_GyroscopeSample_queue_count) % 8u;
        --IMU_GyroscopeSample_queue_count;
        *value = IMU_GyroscopeSample_queue[idx];

        if (IMU_GyroscopeSample_queue_overflow)
        {
            IMU_GyroscopeSample_queue_overflow = false;
            return QueueStatus_Overflow;
        }
        else
        {
            return QueueStatus_Ok;
        }
    }
    /* Begin User Code Section: GyroscopeOffsetCompensator/AngularSpeeds:read End */

    /* End User Code Section: GyroscopeOffsetCompensator/AngularSpeeds:read End */
    return QueueStatus_Empty;
}

bool GyroscopeOffsetCompensator_Read_IsMoving(void)
{
    /* Begin User Code Section: GyroscopeOffsetCompensator/IsMoving:read Start */

    /* End User Code Section: GyroscopeOffsetCompensator/IsMoving:read Start */
    return IMUMovementDetector_IsMoving_variable;
    /* Begin User Code Section: GyroscopeOffsetCompensator/IsMoving:read End */

    /* End User Code Section: GyroscopeOffsetCompensator/IsMoving:read End */
}

uint32_t HardwareCompatibilityChecker_Read_HardwareVersion(void)
{
    /* Begin User Code Section: HardwareCompatibilityChecker/HardwareVersion:read Start */

    /* End User Code Section: HardwareCompatibilityChecker/HardwareVersion:read Start */
    return VersionProvider_Constant_HardwareVersion();
    /* Begin User Code Section: HardwareCompatibilityChecker/HardwareVersion:read End */

    /* End User Code Section: HardwareCompatibilityChecker/HardwareVersion:read End */
}

QueueStatus_t IMUMovementDetector_Read_AngularSpeeds(Vector3D_t* value)
{
    ASSERT(value != NULL);
    /* Begin User Code Section: IMUMovementDetector/AngularSpeeds:read Start */

    /* End User Code Section: IMUMovementDetector/AngularSpeeds:read Start */
    if (IMU_GyroscopeSample_queue1_count > 0u)
    {
        size_t idx = (IMU_GyroscopeSample_queue1_write_index - IMU_GyroscopeSample_queue1_count) % 8u;
        --IMU_GyroscopeSample_queue1_count;
        *value = IMU_GyroscopeSample_queue1[idx];

        if (IMU_GyroscopeSample_queue1_overflow)
        {
            IMU_GyroscopeSample_queue1_overflow = false;
            return QueueStatus_Overflow;
        }
        else
        {
            return QueueStatus_Ok;
        }
    }
    /* Begin User Code Section: IMUMovementDetector/AngularSpeeds:read End */

    /* End User Code Section: IMUMovementDetector/AngularSpeeds:read End */
    return QueueStatus_Empty;
}

QueueStatus_t IMUOrientationEstimator_Read_Acceleration(Vector3D_t* value)
{
    ASSERT(value != NULL);
    /* Begin User Code Section: IMUOrientationEstimator/Acceleration:read Start */

    /* End User Code Section: IMUOrientationEstimator/Acceleration:read Start */
    if (IMU_AccelerometerSample_queue_count > 0u)
    {
        size_t idx = (IMU_AccelerometerSample_queue_write_index - IMU_AccelerometerSample_queue_count) % 32u;
        --IMU_AccelerometerSample_queue_count;
        *value = IMU_AccelerometerSample_queue[idx];

        if (IMU_AccelerometerSample_queue_overflow)
        {
            IMU_AccelerometerSample_queue_overflow = false;
            return QueueStatus_Overflow;
        }
        else
        {
            return QueueStatus_Ok;
        }
    }
    /* Begin User Code Section: IMUOrientationEstimator/Acceleration:read End */

    /* End User Code Section: IMUOrientationEstimator/Acceleration:read End */
    return QueueStatus_Empty;
}

QueueStatus_t IMUOrientationEstimator_Read_AngularSpeeds(Vector3D_t* value)
{
    ASSERT(value != NULL);
    /* Begin User Code Section: IMUOrientationEstimator/AngularSpeeds:read Start */

    /* End User Code Section: IMUOrientationEstimator/AngularSpeeds:read Start */
    if (GyroscopeOffsetCompensator_CompensatedAngularSpeeds_queue_count > 0u)
    {
        size_t idx = (GyroscopeOffsetCompensator_CompensatedAngularSpeeds_queue_write_index - GyroscopeOffsetCompensator_CompensatedAngularSpeeds_queue_count) % 32u;
        --GyroscopeOffsetCompensator_CompensatedAngularSpeeds_queue_count;
        *value = GyroscopeOffsetCompensator_CompensatedAngularSpeeds_queue[idx];

        if (GyroscopeOffsetCompensator_CompensatedAngularSpeeds_queue_overflow)
        {
            GyroscopeOffsetCompensator_CompensatedAngularSpeeds_queue_overflow = false;
            return QueueStatus_Overflow;
        }
        else
        {
            return QueueStatus_Ok;
        }
    }
    /* Begin User Code Section: IMUOrientationEstimator/AngularSpeeds:read End */

    /* End User Code Section: IMUOrientationEstimator/AngularSpeeds:read End */
    return QueueStatus_Empty;
}

float IMUOrientationEstimator_Read_SampleTime(void)
{
    /* Begin User Code Section: IMUOrientationEstimator/SampleTime:read Start */

    /* End User Code Section: IMUOrientationEstimator/SampleTime:read Start */
    return IMU_Constant_SampleTime();
    /* Begin User Code Section: IMUOrientationEstimator/SampleTime:read End */

    /* End User Code Section: IMUOrientationEstimator/SampleTime:read End */
}

rgb_t LEDController_Read_Colors(uint32_t index)
{
    ASSERT(index < 16);
    /* Begin User Code Section: LEDController/Colors:read Start */

    /* End User Code Section: LEDController/Colors:read Start */
    return LedDisplayController_Leds_array[index];
    /* Begin User Code Section: LEDController/Colors:read End */

    /* End User Code Section: LEDController/Colors:read End */
}

uint8_t LEDController_Read_MaxBrightness(void)
{
    /* Begin User Code Section: LEDController/MaxBrightness:read Start */

    /* End User Code Section: LEDController/MaxBrightness:read Start */
    return LedDisplayController_MaxBrightness_variable;
    /* Begin User Code Section: LEDController/MaxBrightness:read End */

    /* End User Code Section: LEDController/MaxBrightness:read End */
}

BluetoothStatus_t LedDisplayController_Read_BluetoothStatus(void)
{
    /* Begin User Code Section: LedDisplayController/BluetoothStatus:read Start */

    /* End User Code Section: LedDisplayController/BluetoothStatus:read Start */
    return BluetoothStatusObserver_ConnectionStatus_variable;
    /* Begin User Code Section: LedDisplayController/BluetoothStatus:read End */

    /* End User Code Section: LedDisplayController/BluetoothStatus:read End */
}

uint8_t LedDisplayController_Read_MainBatteryLevel(void)
{
    /* Begin User Code Section: LedDisplayController/MainBatteryLevel:read Start */

    /* End User Code Section: LedDisplayController/MainBatteryLevel:read Start */
    return BatteryCalculator_MainBatteryLevel_variable;
    /* Begin User Code Section: LedDisplayController/MainBatteryLevel:read End */

    /* End User Code Section: LedDisplayController/MainBatteryLevel:read End */
}

bool LedDisplayController_Read_MainBatteryLow(void)
{
    /* Begin User Code Section: LedDisplayController/MainBatteryLow:read Start */

    /* End User Code Section: LedDisplayController/MainBatteryLow:read Start */
    return BatteryCalculator_MainBatteryLow_variable;
    /* Begin User Code Section: LedDisplayController/MainBatteryLow:read End */

    /* End User Code Section: LedDisplayController/MainBatteryLow:read End */
}

ChargerState_t LedDisplayController_Read_MainBatteryStatus(void)
{
    /* Begin User Code Section: LedDisplayController/MainBatteryStatus:read Start */

    /* End User Code Section: LedDisplayController/MainBatteryStatus:read Start */
    return BatteryCharger_ChargerState_variable;
    /* Begin User Code Section: LedDisplayController/MainBatteryStatus:read End */

    /* End User Code Section: LedDisplayController/MainBatteryStatus:read End */
}

MasterStatus_t LedDisplayController_Read_MasterStatus(void)
{
    /* Begin User Code Section: LedDisplayController/MasterStatus:read Start */

    /* End User Code Section: LedDisplayController/MasterStatus:read Start */
    return MasterStatusObserver_MasterStatus_variable;
    /* Begin User Code Section: LedDisplayController/MasterStatus:read End */

    /* End User Code Section: LedDisplayController/MasterStatus:read End */
}

uint8_t LedDisplayController_Read_MotorBatteryLevel(void)
{
    /* Begin User Code Section: LedDisplayController/MotorBatteryLevel:read Start */

    /* End User Code Section: LedDisplayController/MotorBatteryLevel:read Start */
    return BatteryCalculator_MotorBatteryLevel_variable;
    /* Begin User Code Section: LedDisplayController/MotorBatteryLevel:read End */

    /* End User Code Section: LedDisplayController/MotorBatteryLevel:read End */
}

bool LedDisplayController_Read_MotorBatteryPresent(void)
{
    /* Begin User Code Section: LedDisplayController/MotorBatteryPresent:read Start */

    /* End User Code Section: LedDisplayController/MotorBatteryPresent:read Start */
    return BatteryCalculator_MotorBatteryPresent_variable;
    /* Begin User Code Section: LedDisplayController/MotorBatteryPresent:read End */

    /* End User Code Section: LedDisplayController/MotorBatteryPresent:read End */
}

int16_t LedDisplayController_Read_MotorDriveValues(uint32_t index)
{
    ASSERT(index < 6);
    /* Begin User Code Section: LedDisplayController/MotorDriveValues:read Start */

    /* End User Code Section: LedDisplayController/MotorDriveValues:read Start */
    return MotorPortHandler_DriveStrength_array[index];
    /* Begin User Code Section: LedDisplayController/MotorDriveValues:read End */

    /* End User Code Section: LedDisplayController/MotorDriveValues:read End */
}

rgb_t LedDisplayController_Read_RingLeds(uint32_t index)
{
    ASSERT(index < 12);
    /* Begin User Code Section: LedDisplayController/RingLeds:read Start */

    /* End User Code Section: LedDisplayController/RingLeds:read Start */
    return RingLedDisplay_LedColor_array[index];
    /* Begin User Code Section: LedDisplayController/RingLeds:read End */

    /* End User Code Section: LedDisplayController/RingLeds:read End */
}

uint8_t MasterCommunicationInterface_Read_DeviceAddress(void)
{
    /* Begin User Code Section: MasterCommunicationInterface/DeviceAddress:read Start */

    /* End User Code Section: MasterCommunicationInterface/DeviceAddress:read Start */
    return ProjectConfiguration_Constant_DeviceAddress();
    /* Begin User Code Section: MasterCommunicationInterface/DeviceAddress:read End */

    /* End User Code Section: MasterCommunicationInterface/DeviceAddress:read End */
}

uint32_t MasterStatusObserver_Read_ExpectedStartupTime(void)
{
    /* Begin User Code Section: MasterStatusObserver/ExpectedStartupTime:read Start */

    /* End User Code Section: MasterStatusObserver/ExpectedStartupTime:read Start */
    return ProjectConfiguration_Constant_ExpectedStartupTime();
    /* Begin User Code Section: MasterStatusObserver/ExpectedStartupTime:read End */

    /* End User Code Section: MasterStatusObserver/ExpectedStartupTime:read End */
}

bool MasterStatusObserver_Read_IsColdStart(void)
{
    /* Begin User Code Section: MasterStatusObserver/IsColdStart:read Start */

    /* End User Code Section: MasterStatusObserver/IsColdStart:read Start */
    return StartupReasonProvider_IsColdStart_variable;
    /* Begin User Code Section: MasterStatusObserver/IsColdStart:read End */

    /* End User Code Section: MasterStatusObserver/IsColdStart:read End */
}

uint32_t MasterStatusObserver_Read_UpdateTimeout(void)
{
    /* Begin User Code Section: MasterStatusObserver/UpdateTimeout:read Start */

    /* End User Code Section: MasterStatusObserver/UpdateTimeout:read Start */
    return ProjectConfiguration_Constant_ExpectedUpdateTime();
    /* Begin User Code Section: MasterStatusObserver/UpdateTimeout:read End */

    /* End User Code Section: MasterStatusObserver/UpdateTimeout:read End */
}

SlotData_t McuStatusCollector_Read_SlotData(uint32_t index)
{
    ASSERT(index < 16);
    /* Begin User Code Section: McuStatusCollector/SlotData:read Start */

    /* End User Code Section: McuStatusCollector/SlotData:read Start */
    return McuStatusSlots_SlotData_array[index];
    /* Begin User Code Section: McuStatusCollector/SlotData:read End */

    /* End User Code Section: McuStatusCollector/SlotData:read End */
}

void McuStatusSlots_Read_Acceleration(IMU_RawSample_t* value)
{
    ASSERT(value != NULL);
    /* Begin User Code Section: McuStatusSlots/Acceleration:read Start */

    /* End User Code Section: McuStatusSlots/Acceleration:read Start */
    *value = IMU_RawAccelerometerSample_variable;
    /* Begin User Code Section: McuStatusSlots/Acceleration:read End */

    /* End User Code Section: McuStatusSlots/Acceleration:read End */
}

void McuStatusSlots_Read_AngularSpeeds(IMU_RawSample_t* value)
{
    ASSERT(value != NULL);
    /* Begin User Code Section: McuStatusSlots/AngularSpeeds:read Start */

    /* End User Code Section: McuStatusSlots/AngularSpeeds:read Start */
    *value = IMU_RawGyroscopeSample_variable;
    /* Begin User Code Section: McuStatusSlots/AngularSpeeds:read End */

    /* End User Code Section: McuStatusSlots/AngularSpeeds:read End */
}

uint8_t McuStatusSlots_Read_MainBatteryLevel(void)
{
    /* Begin User Code Section: McuStatusSlots/MainBatteryLevel:read Start */

    /* End User Code Section: McuStatusSlots/MainBatteryLevel:read Start */
    return BatteryCalculator_MainBatteryLevel_variable;
    /* Begin User Code Section: McuStatusSlots/MainBatteryLevel:read End */

    /* End User Code Section: McuStatusSlots/MainBatteryLevel:read End */
}

ChargerState_t McuStatusSlots_Read_MainBatteryStatus(void)
{
    /* Begin User Code Section: McuStatusSlots/MainBatteryStatus:read Start */

    /* End User Code Section: McuStatusSlots/MainBatteryStatus:read Start */
    return BatteryCharger_ChargerState_variable;
    /* Begin User Code Section: McuStatusSlots/MainBatteryStatus:read End */

    /* End User Code Section: McuStatusSlots/MainBatteryStatus:read End */
}

uint8_t McuStatusSlots_Read_MotorBatteryLevel(void)
{
    /* Begin User Code Section: McuStatusSlots/MotorBatteryLevel:read Start */

    /* End User Code Section: McuStatusSlots/MotorBatteryLevel:read Start */
    return BatteryCalculator_MotorBatteryLevel_variable;
    /* Begin User Code Section: McuStatusSlots/MotorBatteryLevel:read End */

    /* End User Code Section: McuStatusSlots/MotorBatteryLevel:read End */
}

bool McuStatusSlots_Read_MotorBatteryPresent(void)
{
    /* Begin User Code Section: McuStatusSlots/MotorBatteryPresent:read Start */

    /* End User Code Section: McuStatusSlots/MotorBatteryPresent:read Start */
    return BatteryCalculator_MotorBatteryPresent_variable1;
    /* Begin User Code Section: McuStatusSlots/MotorBatteryPresent:read End */

    /* End User Code Section: McuStatusSlots/MotorBatteryPresent:read End */
}

void McuStatusSlots_Read_Orientation(Orientation3D_t* value)
{
    ASSERT(value != NULL);
    /* Begin User Code Section: McuStatusSlots/Orientation:read Start */

    /* End User Code Section: McuStatusSlots/Orientation:read Start */
    *value = IMUOrientationEstimator_OrientationEulerDegrees_variable1;
    /* Begin User Code Section: McuStatusSlots/Orientation:read End */

    /* End User Code Section: McuStatusSlots/Orientation:read End */
}

float McuStatusSlots_Read_YawAngle(void)
{
    /* Begin User Code Section: McuStatusSlots/YawAngle:read Start */

    /* End User Code Section: McuStatusSlots/YawAngle:read Start */
    return IMUOrientationEstimator_OrientationEulerDegrees_variable.yaw;
    /* Begin User Code Section: McuStatusSlots/YawAngle:read End */

    /* End User Code Section: McuStatusSlots/YawAngle:read End */
}

Current_t MotorCurrentFilter_Read_RawCurrent(uint32_t index)
{
    ASSERT(index < 6);
    /* Begin User Code Section: MotorCurrentFilter/RawCurrent:read Start */

    /* End User Code Section: MotorCurrentFilter/RawCurrent:read Start */
    return ADC_MotorCurrent_array[index];
    /* Begin User Code Section: MotorCurrentFilter/RawCurrent:read End */

    /* End User Code Section: MotorCurrentFilter/RawCurrent:read End */
}

int16_t MotorDerating_Read_ControlValue(uint32_t index)
{
    ASSERT(index < 6);
    /* Begin User Code Section: MotorDerating/ControlValue:read Start */

    /* End User Code Section: MotorDerating/ControlValue:read Start */
    return MotorPortHandler_DriveStrength_array[index];
    /* Begin User Code Section: MotorDerating/ControlValue:read End */

    /* End User Code Section: MotorDerating/ControlValue:read End */
}

Current_t MotorDerating_Read_MaxMotorCurrent(uint32_t index)
{
    ASSERT(index < 6);
    /* Begin User Code Section: MotorDerating/MaxMotorCurrent:read Start */

    /* End User Code Section: MotorDerating/MaxMotorCurrent:read Start */
    return MotorPortHandler_MaxAllowedCurrent_array[index];
    /* Begin User Code Section: MotorDerating/MaxMotorCurrent:read End */

    /* End User Code Section: MotorDerating/MaxMotorCurrent:read End */
}

Current_t MotorDerating_Read_MotorCurrent(uint32_t index)
{
    ASSERT(index < 6);
    /* Begin User Code Section: MotorDerating/MotorCurrent:read Start */

    /* End User Code Section: MotorDerating/MotorCurrent:read Start */
    return MotorCurrentFilter_FilteredCurrent_array[index];
    /* Begin User Code Section: MotorDerating/MotorCurrent:read End */

    /* End User Code Section: MotorDerating/MotorCurrent:read End */
}

Temperature_t MotorDerating_Read_MotorTemperature(uint32_t index)
{
    ASSERT(index < 6);
    /* Begin User Code Section: MotorDerating/MotorTemperature:read Start */

    /* End User Code Section: MotorDerating/MotorTemperature:read Start */
    return MotorThermalModel_Temperature_array[index];
    /* Begin User Code Section: MotorDerating/MotorTemperature:read End */

    /* End User Code Section: MotorDerating/MotorTemperature:read End */
}

void MotorDerating_Read_Parameters(MotorDeratingParameters_t* value)
{
    ASSERT(value != NULL);
    /* Begin User Code Section: MotorDerating/Parameters:read Start */

    /* End User Code Section: MotorDerating/Parameters:read Start */
    ProjectConfiguration_Constant_MotorDeratingParameters(value);
    /* Begin User Code Section: MotorDerating/Parameters:read End */

    /* End User Code Section: MotorDerating/Parameters:read End */
}

void MotorPortHandler_Read_DriveRequest(uint32_t index, DriveRequest_t* value)
{
    ASSERT(index < 6);
    ASSERT(value != NULL);
    /* Begin User Code Section: MotorPortHandler/DriveRequest:read Start */

    /* End User Code Section: MotorPortHandler/DriveRequest:read Start */
    *value = CommWrapper_MotorPorts_DriveRequest_array[index];
    /* Begin User Code Section: MotorPortHandler/DriveRequest:read End */

    /* End User Code Section: MotorPortHandler/DriveRequest:read End */
}

void MotorPortHandler_Read_PortConfig(uint32_t index, MotorPortGpios_t* value)
{
    ASSERT(index < 6);
    ASSERT(value != NULL);
    /* Begin User Code Section: MotorPortHandler/PortConfig:read Start */

    /* End User Code Section: MotorPortHandler/PortConfig:read Start */
    ProjectConfiguration_Constant_MotorPortGpios(index, value);
    /* Begin User Code Section: MotorPortHandler/PortConfig:read End */

    /* End User Code Section: MotorPortHandler/PortConfig:read End */
}

Percentage_t MotorPortHandler_Read_RelativeMotorCurrent(uint32_t index)
{
    ASSERT(index < 6);
    /* Begin User Code Section: MotorPortHandler/RelativeMotorCurrent:read Start */

    /* End User Code Section: MotorPortHandler/RelativeMotorCurrent:read Start */
    return MotorDerating_RelativeMotorCurrent_array[index];
    /* Begin User Code Section: MotorPortHandler/RelativeMotorCurrent:read End */

    /* End User Code Section: MotorPortHandler/RelativeMotorCurrent:read End */
}

Current_t MotorThermalModel_Read_MotorCurrent(uint32_t index)
{
    ASSERT(index < 6);
    /* Begin User Code Section: MotorThermalModel/MotorCurrent:read Start */

    /* End User Code Section: MotorThermalModel/MotorCurrent:read Start */
    return MotorCurrentFilter_FilteredCurrent_array[index];
    /* Begin User Code Section: MotorThermalModel/MotorCurrent:read End */

    /* End User Code Section: MotorThermalModel/MotorCurrent:read End */
}

void MotorThermalModel_Read_ThermalParameters(MotorThermalParameters_t* value)
{
    ASSERT(value != NULL);
    /* Begin User Code Section: MotorThermalModel/ThermalParameters:read Start */

    /* End User Code Section: MotorThermalModel/ThermalParameters:read Start */
    ProjectConfiguration_Constant_MotorThermalParameters(value);
    /* Begin User Code Section: MotorThermalModel/ThermalParameters:read End */

    /* End User Code Section: MotorThermalModel/ThermalParameters:read End */
}

uint32_t RingLedDisplay_Read_ExpectedStartupTime(void)
{
    /* Begin User Code Section: RingLedDisplay/ExpectedStartupTime:read Start */

    /* End User Code Section: RingLedDisplay/ExpectedStartupTime:read Start */
    return ProjectConfiguration_Constant_ExpectedStartupTime();
    /* Begin User Code Section: RingLedDisplay/ExpectedStartupTime:read End */

    /* End User Code Section: RingLedDisplay/ExpectedStartupTime:read End */
}

MasterStatus_t RingLedDisplay_Read_MasterStatus(void)
{
    /* Begin User Code Section: RingLedDisplay/MasterStatus:read Start */

    /* End User Code Section: RingLedDisplay/MasterStatus:read Start */
    return MasterStatusObserver_MasterStatus_variable;
    /* Begin User Code Section: RingLedDisplay/MasterStatus:read End */

    /* End User Code Section: RingLedDisplay/MasterStatus:read End */
}

RingLedScenario_t RingLedDisplay_Read_Scenario(void)
{
    /* Begin User Code Section: RingLedDisplay/Scenario:read Start */

    /* End User Code Section: RingLedDisplay/Scenario:read Start */
    return CommWrapper_LedDisplay_Scenario_variable;
    /* Begin User Code Section: RingLedDisplay/Scenario:read End */

    /* End User Code Section: RingLedDisplay/Scenario:read End */
}

rgb_t RingLedDisplay_Read_UserColors(uint32_t index)
{
    ASSERT(index < 12);
    /* Begin User Code Section: RingLedDisplay/UserColors:read Start */

    /* End User Code Section: RingLedDisplay/UserColors:read Start */
    return CommWrapper_LedDisplay_UserFrame_array[index];
    /* Begin User Code Section: RingLedDisplay/UserColors:read End */

    /* End User Code Section: RingLedDisplay/UserColors:read End */
}

bool RingLedDisplay_Read_WaitForMasterStartup(void)
{
    /* Begin User Code Section: RingLedDisplay/WaitForMasterStartup:read Start */

    /* End User Code Section: RingLedDisplay/WaitForMasterStartup:read Start */
    return StartupReasonProvider_IsColdStart_variable;
    /* Begin User Code Section: RingLedDisplay/WaitForMasterStartup:read End */

    /* End User Code Section: RingLedDisplay/WaitForMasterStartup:read End */
}

uint8_t SensorPortHandler_Read_AdcData(uint32_t index)
{
    ASSERT(index < 4);
    /* Begin User Code Section: SensorPortHandler/AdcData:read Start */

    /* End User Code Section: SensorPortHandler/AdcData:read Start */
    return ADC_Sensor_ADC_array[index];
    /* Begin User Code Section: SensorPortHandler/AdcData:read End */

    /* End User Code Section: SensorPortHandler/AdcData:read End */
}

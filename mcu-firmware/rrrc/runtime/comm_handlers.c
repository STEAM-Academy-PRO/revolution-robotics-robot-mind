#include "../rrrc_worklogic.h"
#include "comm_handlers.h"

static Comm_Status_t PingMessageHandler_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount);

static Comm_Status_t CommWrapper_IMUOrientationEstimator_Reset_Start(ConstByteArray_t commandPayload,
  ByteArray_t response, uint8_t* responseCount)
{
    (void) response;
    (void) responseCount;

    if (commandPayload.count != 0u)
    {
        return Comm_Status_Error_PayloadLengthError;
    }

    IMUOrientationEstimator_Reset();
    return Comm_Status_Ok;
}

/* These commands relate to RevvyControl in pi-firmware/revvy/mcu/rrrc_control.py */
Comm_CommandHandler_t communicationHandlers[COMM_HANDLER_COUNT] =
{
    /* other commands */
    [0x00u] = { .Start = &PingMessageHandler_Start, .GetResult = NULL, .ExecutionInProgress = false },
    [0x01u] = { .Start = &CommWrapper_VersionProvider_Run_Command_ReadHardwareVersion_Start, .GetResult = NULL, .ExecutionInProgress = false },
    [0x02u] = { .Start = &CommWrapper_VersionProvider_Run_Command_ReadFirmwareVersion_Start, .GetResult = NULL, .ExecutionInProgress = false },
    [0x04u] = { .Start = &MasterStatusObserver_Run_Command_SetMasterStatus_Start, .GetResult = NULL, .ExecutionInProgress = false },
    [0x05u] = { .Start = &BluetoothStatusObserver_Run_Command_SetBluetoothStatus_Start, .GetResult = NULL, .ExecutionInProgress = false },

    /* [0x06 - 0x0A]: reserved for bootloader */
    [0x06u] = { .Start = &CommWrapper_Bootloader_Run_Command_GetOperationMode_Start, .GetResult = NULL, .ExecutionInProgress = false },
    [0x0Bu] = { .Start = &CommWrapper_Bootloader_Run_Command_RebootToBootloader_Start, .GetResult = NULL, .ExecutionInProgress = false },

    /* motor commands */
    [0x10u] = { .Start = &CommWrapper_MotorPorts_Run_Command_GetPortAmount_Start, .GetResult = NULL, .ExecutionInProgress = false },
    [0x11u] = { .Start = &CommWrapper_MotorPorts_Run_Command_GetPortTypes_Start, .GetResult = NULL, .ExecutionInProgress = false },
    [0x12u] = { .Start = &CommWrapper_MotorPorts_Run_Command_SetPortType_Start, .GetResult = &CommWrapper_MotorPorts_Run_Command_SetPortType_GetResult, .ExecutionInProgress = false },
    [0x13u] = { .Start = &CommWrapper_MotorPorts_Run_Command_SetPortConfig_Start, .GetResult = &CommWrapper_MotorPorts_Run_Command_SetPortConfig_GetResult, .ExecutionInProgress = false },
    [0x14u] = { .Start = &CommWrapper_MotorPorts_Run_Command_SetControlValue_Start, .GetResult = NULL, .ExecutionInProgress = false },
    [0x15u] = { .Start = &CommWrapper_MotorPorts_Run_Command_TestMotorOnPort_Start, .GetResult = CommWrapper_MotorPorts_Run_Command_TestMotorOnPort_GetResult, .ExecutionInProgress = false },

    /* sensor commands */
    [0x20u] = { .Start = &CommWrapper_SensorPorts_Run_Command_GetPortAmount_Start, .GetResult = NULL, .ExecutionInProgress = false },
    [0x21u] = { .Start = &CommWrapper_SensorPorts_Run_Command_GetPortTypes_Start, .GetResult = NULL, .ExecutionInProgress = false },
    [0x22u] = { .Start = &CommWrapper_SensorPorts_Run_Command_SetPortType_Start, .GetResult = &CommWrapper_SensorPorts_Run_Command_SetPortType_GetResult, .ExecutionInProgress = false },
    [0x23u] = { .Start = &CommWrapper_SensorPorts_Run_Command_SetPortConfig_Start, .GetResult = &CommWrapper_SensorPorts_Run_Command_SetPortConfig_GetResult, .ExecutionInProgress = false },
    [0x24u] = { .Start = &CommWrapper_SensorPorts_Run_Command_ReadSensorInfo_Start, .GetResult = NULL, .ExecutionInProgress = false },
    [0x25u] = { .Start = &CommWrapper_SensorPorts_Run_Command_TestSensorOnPort_Start, .GetResult = CommWrapper_SensorPorts_Run_Command_TestSensorOnPort_GetResult, .ExecutionInProgress = false },

    /* led ring commands */
    [0x30u] = { .Start = &CommWrapper_LedDisplay_Run_Command_GetScenarioTypes_Start, .GetResult = NULL, .ExecutionInProgress = false },
    [0x31u] = { .Start = &CommWrapper_LedDisplay_Run_Command_SetScenarioType_Start, .GetResult = NULL, .ExecutionInProgress = false },
    [0x32u] = { .Start = &CommWrapper_LedDisplay_Run_Command_GetRingLedAmount_Start, .GetResult = NULL, .ExecutionInProgress = false },
    [0x33u] = { .Start = &CommWrapper_LedDisplay_Run_Command_SetUserFrame_Start, .GetResult = NULL, .ExecutionInProgress = false },

    /* MCU status updater commands */
    [0x3Au] = { .Start = &CommWrapper_McuStatusCollector_Run_Command_Reset_Start, .GetResult = NULL, .ExecutionInProgress = false },
    [0x3Bu] = { .Start = &CommWrapper_McuStatusCollector_Run_Command_ControlSlot_Start, .GetResult = NULL, .ExecutionInProgress = false },
    [0x3Cu] = { .Start = &CommWrapper_McuStatusCollector_Run_Command_ReadStatus_Start, .GetResult = NULL, .ExecutionInProgress = false },

    /* Error storage commands */
    [0x3Du] = { .Start = &CommWrapper_ErrorStorage_Run_Command_ReadCount_Start, .GetResult = NULL, .ExecutionInProgress = false }, /* Read stored error count */
    [0x3Eu] = { .Start = &CommWrapper_ErrorStorage_Run_Command_ReadErrors_Start, .GetResult = NULL, .ExecutionInProgress = false }, /* Read errors starting with the given index */
    [0x3Fu] = { .Start = &CommWrapper_ErrorStorage_Run_Command_ClearMemory_Start, .GetResult = NULL, .ExecutionInProgress = false }, /* Clear error memory */
    [0x40u] = { .Start = &CommWrapper_ErrorStorage_Run_Command_StoreTestError_Start, .GetResult = NULL, .ExecutionInProgress = false }, /* Record a test error */

    [0x41u] = { .Start = &CommWrapper_IMUOrientationEstimator_Reset_Start, .GetResult = NULL, .ExecutionInProgress = false },
};

static Comm_Status_t PingMessageHandler_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount)
{
    (void) response;
    (void) responseCount;

    if (commandPayload.count != 0u)
    {
        return Comm_Status_Error_PayloadLengthError;
    }

    return Comm_Status_Ok;
}

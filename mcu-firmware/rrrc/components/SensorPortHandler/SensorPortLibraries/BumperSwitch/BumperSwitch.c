#include "BumperSwitch.h"

#include "FreeRTOS.h"
#include "task.h"

typedef struct
{
    uint8_t threshold;
    uint8_t analogValue;
    bool was_pressed;
} SensorLibrary_BumperSwitch_Data_t;

SensorLibraryStatus_t BumperSwitch_Load(SensorPort_t* sensorPort)
{
    SensorLibrary_BumperSwitch_Data_t* libdata = SensorPortHandler_Call_Allocate(sizeof(SensorLibrary_BumperSwitch_Data_t));
    libdata->threshold = 75u; /* sensor ADC input has a range of 0..5V, bumper switch is 3V, set threshold to half of that */
    libdata->was_pressed = false;

    sensorPort->libraryData = libdata;
    SensorPort_SetGreenLed(sensorPort, true);
    return SensorLibraryStatus_Ok;
}

void BumperSwitch_Unload(SensorPort_t* sensorPort, OnDeInitCompletedCb cb)
{
    SensorPort_SetOrangeLed(sensorPort, false);
    SensorPort_SetGreenLed(sensorPort, false);
    SensorPortHandler_Call_Free(&sensorPort->libraryData);
    cb(sensorPort, true);
}

SensorLibraryStatus_t BumperSwitch_Update(SensorPort_t* sensorPort)
{
    SensorLibrary_BumperSwitch_Data_t* libdata = (SensorLibrary_BumperSwitch_Data_t*) sensorPort->libraryData;

    if (libdata->analogValue > libdata->threshold)
    {
        SensorPort_SetOrangeLed(sensorPort, true);
    }
    else
    {
        SensorPort_SetOrangeLed(sensorPort, false);
    }

    return SensorLibraryStatus_Ok;
}

SensorLibraryStatus_t BumperSwitch_UpdateConfiguration(SensorPort_t* sensorPort, const uint8_t* data, uint8_t size)
{
    (void) sensorPort;
    (void) data;
    (void) size;

    return SensorLibraryStatus_Ok;
}

SensorLibraryStatus_t BumperSwitch_InterruptCallback(SensorPort_t* sensorPort, bool status)
{
    (void) sensorPort;
    (void) status;
    return SensorLibraryStatus_Ok;
}

SensorLibraryStatus_t BumperSwitch_UpdateAnalogData(SensorPort_t* sensorPort, uint8_t rawValue)
{
    SensorLibrary_BumperSwitch_Data_t* libdata = (SensorLibrary_BumperSwitch_Data_t*) sensorPort->libraryData;
    portENTER_CRITICAL();
    libdata->analogValue = rawValue;
    if (rawValue > libdata->threshold)
    {
        libdata->was_pressed = true;
    }
    uint8_t data[] = { rawValue > libdata->threshold ? 1u : 0u, rawValue };
    portEXIT_CRITICAL();

    SensorPortHandler_Call_UpdatePortStatus(sensorPort->port_idx, (ByteArray_t){data, sizeof(data)});
    return SensorLibraryStatus_Ok;
}

void BumperSwitch_ReadSensorInfo(SensorPort_t* sensorPort, uint8_t page, uint8_t* buffer, uint8_t size, uint8_t* count)
{
    (void) sensorPort;
    (void) page;
    (void) buffer;
    (void) size;

    *count = 0u;
}

static bool BumperSwitch_TestSensorOnPort(SensorPort_t *port, SensorOnPortStatus_t *result)
{
  *result = SensorOnPortStatus_Unknown;
  return true;
}

const SensorLibrary_t sensor_library_bumper_switch =
{
    .Name                = "BumperSwitch",
    .Load                = &BumperSwitch_Load,
    .Unload              = &BumperSwitch_Unload,
    .Update              = &BumperSwitch_Update,
    .UpdateConfiguration = &BumperSwitch_UpdateConfiguration,
    .UpdateAnalogData    = &BumperSwitch_UpdateAnalogData,
    .InterruptHandler    = &BumperSwitch_InterruptCallback,
    .ReadSensorInfo      = &BumperSwitch_ReadSensorInfo,
    .TestSensorOnPort    = &BumperSwitch_TestSensorOnPort
};

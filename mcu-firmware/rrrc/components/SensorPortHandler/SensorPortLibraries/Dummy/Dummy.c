#include "Dummy.h"

SensorLibraryStatus_t DummySensor_Load(SensorPort_t* sensorPort)
{
    (void) sensorPort;
    return SensorLibraryStatus_Ok;
}

SensorLibraryUnloadStatus_t DummySensor_Unload(SensorPort_t* sensorPort)
{
    (void) sensorPort;
    return SensorLibraryUnloadStatus_Done;
}

SensorLibraryStatus_t DummySensor_Update(SensorPort_t* sensorPort)
{
    (void) sensorPort;
    return SensorLibraryStatus_Ok;
}

SensorLibraryStatus_t DummySensor_UpdateConfiguration(SensorPort_t* sensorPort, const uint8_t* data, uint8_t size)
{
    (void) sensorPort;
    (void) data;
    (void) size;
    return SensorLibraryStatus_Ok;
}

SensorLibraryStatus_t DummySensor_UpdateAnalogData(SensorPort_t* sensorPort, uint8_t rawValue)
{
    (void) sensorPort;
    (void) rawValue;
    return SensorLibraryStatus_Ok;
}

SensorLibraryStatus_t DummySensor_InterruptCallback(SensorPort_t* sensorPort, bool status)
{
    (void) sensorPort;
    (void) status;
    return SensorLibraryStatus_Ok;
}

void DummySensor_ReadSensorInfo(SensorPort_t* sensorPort, uint8_t page, uint8_t* buffer, uint8_t size, uint8_t* count)
{
    (void) sensorPort;
    (void) page;
    (void) buffer;
    (void) size;

    *count = 0u;
}

static bool DummySensor_TestSensorOnPort(SensorPort_t *port, SensorOnPortStatus_t *result)
{
  *result = SensorOnPortStatus_NotPresent;
  return true;
}

const SensorLibrary_t sensor_library_dummy =
{
    .Name                = "NotConfigured",
    .Load                = &DummySensor_Load,
    .Unload              = &DummySensor_Unload,
    .Update              = &DummySensor_Update,
    .UpdateConfiguration = &DummySensor_UpdateConfiguration,
    .UpdateAnalogData    = &DummySensor_UpdateAnalogData,
    .InterruptHandler    = &DummySensor_InterruptCallback,
    .ReadSensorInfo      = &DummySensor_ReadSensorInfo,
    .TestSensorOnPort    = &DummySensor_TestSensorOnPort
};

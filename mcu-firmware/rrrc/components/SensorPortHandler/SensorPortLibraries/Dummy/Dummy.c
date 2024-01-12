#include "Dummy.h"

SensorLibraryStatus_t DummySensor_Init(SensorPort_t* sensorPort)
{
    (void) sensorPort;
    return SensorLibraryStatus_Ok;
}

void DummySensor_DeInit(SensorPort_t* sensorPort, OnDeInitCompletedCb cb)
{
    cb(sensorPort, true);
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

static const SensorLibrary_t sensor_library_dummy = 
{
    .name                = "NotConfigured",
    .Init                = &DummySensor_Init,
    .DeInit              = &DummySensor_DeInit,
    .Update              = &DummySensor_Update,
    .UpdateConfiguration = &DummySensor_UpdateConfiguration,
    .UpdateAnalogData    = &DummySensor_UpdateAnalogData,
    .InterruptHandler    = &DummySensor_InterruptCallback,
    .ReadSensorInfo      = &DummySensor_ReadSensorInfo,
    .TestSensorOnPort    = &DummySensor_TestSensorOnPort
};

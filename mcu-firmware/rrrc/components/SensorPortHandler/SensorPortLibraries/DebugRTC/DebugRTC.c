#include "DebugRTC.h"
#include "utils.h"

#define I2C_ADDRESS ((uint8_t) 0x68u) //0110 1000

typedef struct {
    uint8_t data;
    bool reading;
} SensorLibrary_DebugRTC_Data_t;

static void rxcomplete(I2CMasterInstance_t* instance, size_t transferred)
{
    SensorPort_t *port = CONTAINER_OF(instance, SensorPort_t, sercom.i2cm.sercom_instance);
    SensorLibrary_DebugRTC_Data_t* libdata = port->libraryData;

    if (transferred == 1u)
    {
        SensorPort_SetOrangeLed(port, ((libdata->data % 2) == 0));
    }

    libdata->reading = false;
}

SensorLibraryStatus_t DebugRTC_Init(SensorPort_t* sensorPort)
{
    SensorPort_SetVccIo(sensorPort, Sensor_VccIo_5V);
    SensorPort_I2C_Enable(sensorPort, 100);
    SensorPort_SetOrangeLed(sensorPort, false);

    SensorLibrary_DebugRTC_Data_t* libdata = SensorPortHandler_Call_Allocate(sizeof(SensorLibrary_DebugRTC_Data_t));
    libdata->reading = false;
    libdata->data = 0u;

    sensorPort->libraryData = libdata;

    return SensorLibraryStatus_Ok;
}

void DebugRTC_DeInit(SensorPort_t* sensorPort, OnDeInitCompletedCb cb)
{
    SensorPort_SetGreenLed(sensorPort, false);
    SensorPort_SetOrangeLed(sensorPort, false);
    SensorPort_SetVccIo(sensorPort, Sensor_VccIo_3V3);
    SensorPort_I2C_Disable(sensorPort);
    SensorPortHandler_Call_Free(&sensorPort->libraryData);
    cb(sensorPort, true);
}

SensorLibraryStatus_t DebugRTC_Update(SensorPort_t* sensorPort)
{
    SensorLibrary_DebugRTC_Data_t* libdata = sensorPort->libraryData;
    if (!libdata->reading)
    {
        libdata->reading = true;
        if (SensorPort_I2C_StartRegRead(sensorPort, I2C_ADDRESS, 0x00, &libdata->data, 1,&rxcomplete) == SensorPort_I2C_Error)
        {
            SensorPort_SetGreenLed(sensorPort, false);
            SensorPort_SetOrangeLed(sensorPort, false);
            libdata->reading = false;
        }
        else
        {
            SensorPort_SetGreenLed(sensorPort, true);
        }
    }
    return SensorLibraryStatus_Ok;
}

SensorLibraryStatus_t DebugRTC_UpdateConfiguration(SensorPort_t* sensorPort, const uint8_t* data, uint8_t size)
{
    (void) sensorPort;
    (void) data;
    (void) size;

    return SensorLibraryStatus_Ok;
}

SensorLibraryStatus_t DebugRTC_UpdateAnalogData(SensorPort_t* sensorPort, uint8_t rawValue)
{
    (void) sensorPort;
    (void) rawValue;

    return SensorLibraryStatus_Ok;
}

SensorLibraryStatus_t DebugRTC_InterruptCallback(SensorPort_t* sensorPort, bool status)
{
    (void) sensorPort;
    (void) status;

    return SensorLibraryStatus_Ok;
}

void DebugRTC_ReadSensorInfo(SensorPort_t* sensorPort, uint8_t page, uint8_t* buffer, uint8_t size, uint8_t* count)
{
    (void) sensorPort;
    (void) page;
    (void) buffer;
    (void) size;

    *count = 0u;
}

static bool DebugRTC_TestSensorOnPort(SensorPort_t *port, SensorOnPortStatus_t *result)
{
  *result = SensorOnPortStatus_Unknown;
  return true;
}

const SensorLibrary_t sensor_library_debug_rtc =
{
    .name                = "DebugRTC",
    .Init                = &DebugRTC_Init,
    .DeInit              = &DebugRTC_DeInit,
    .Update              = &DebugRTC_Update,
    .UpdateConfiguration = &DebugRTC_UpdateConfiguration,
    .UpdateAnalogData    = &DebugRTC_UpdateAnalogData,
    .InterruptHandler    = &DebugRTC_InterruptCallback,
    .ReadSensorInfo      = &DebugRTC_ReadSensorInfo,
    .TestSensorOnPort    = &DebugRTC_TestSensorOnPort
};

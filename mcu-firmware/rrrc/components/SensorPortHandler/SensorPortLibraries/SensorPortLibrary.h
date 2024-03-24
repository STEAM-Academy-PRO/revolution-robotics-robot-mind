#ifndef SENSOR_PORT_LIBRARY_H_
#define SENSOR_PORT_LIBRARY_H_

struct _SensorLibrary_t;

#include "../SensorPortHandlerInternal.h"

typedef enum {
    SensorLibraryStatus_Ok,
    SensorLibraryStatus_Pending,
    SensorLibraryStatus_LengthError,
    SensorLibraryStatus_ValueError
} SensorLibraryStatus_t;

typedef enum {
    SensorOnPortStatus_NotPresent,
    SensorOnPortStatus_Present,
    SensorOnPortStatus_Unknown,
    SensorOnPortStatus_Error,
} SensorOnPortStatus_t;

typedef enum {
    SensorLibraryUnloadStatus_Pending,
    SensorLibraryUnloadStatus_Done,
} SensorLibraryUnloadStatus_t;

typedef struct _SensorLibrary_t
{
    const char* Name;
    SensorLibraryStatus_t (*Load)(struct _SensorPort_t* sensorPort);
    SensorLibraryUnloadStatus_t (*Unload)(struct _SensorPort_t* sensorPort);
    SensorLibraryStatus_t (*Update)(struct _SensorPort_t* sensorPort);

    SensorLibraryStatus_t (*UpdateConfiguration)(struct _SensorPort_t* sensorPort, const uint8_t* data, uint8_t size);

    SensorLibraryStatus_t (*InterruptHandler)(struct _SensorPort_t* sensorPort, bool state);
    SensorLibraryStatus_t (*UpdateAnalogData)(struct _SensorPort_t* sensorPort, uint8_t rawValue);

    void (*ReadSensorInfo)(struct _SensorPort_t* sensorPort, uint8_t page, uint8_t* data, uint8_t size, uint8_t* count);
    bool (*TestSensorOnPort)(struct _SensorPort_t *sensorPort, SensorOnPortStatus_t *result);
} SensorLibrary_t;

#endif /* SENSOR_PORT_LIBRARY_H_ */

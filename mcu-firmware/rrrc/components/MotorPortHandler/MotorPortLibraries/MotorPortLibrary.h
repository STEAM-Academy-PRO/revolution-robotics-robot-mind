#ifndef MOTOR_PORT_LIBRARY_H_
#define MOTOR_PORT_LIBRARY_H_

struct _MotorLibrary_t;

#include "../MotorPortHandlerInternal.h"

typedef enum {
    MotorLibraryStatus_Ok,
    MotorLibraryStatus_InputError
} MotorLibraryStatus_t;

typedef struct
{
    const char* name;
    MotorLibraryStatus_t (*Init)(MotorPort_t* motorPort);
    MotorLibraryStatus_t (*DeInit)(MotorPort_t* motorPort);
    MotorLibraryStatus_t (*Update)(MotorPort_t* motorPort);

    void (*Gpio0Callback)(void* port);
    void (*Gpio1Callback)(void* port);

    MotorLibraryStatus_t (*UpdateConfiguration)(MotorPort_t* motorPort, const uint8_t* data, uint8_t size);

    MotorLibraryStatus_t (*CreateDriveRequest)(const MotorPort_t* motorPort, const uint8_t* data, uint8_t size, DriveRequest_t* request);
} MotorLibrary_t;

#endif /* MOTOR_PORT_LIBRARY_H_ */

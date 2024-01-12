/*
 * Dummy.c
 *
 * Created: 09/05/2019 16:18:37
 *  Author: D�niel Buga
 */
#include "Dummy.h"

MotorLibraryStatus_t Dummy_Init(MotorPort_t* motorPort)
{
    (void) motorPort;
    return MotorLibraryStatus_Ok;
}

MotorLibraryStatus_t Dummy_DeInit(MotorPort_t* motorPort)
{
    (void) motorPort;
    return MotorLibraryStatus_Ok;
}

MotorLibraryStatus_t Dummy_Update(MotorPort_t* motorPort)
{
    (void) motorPort;
    return MotorLibraryStatus_Ok;
}

void Dummy_Gpio0Callback(void* port)
{
    (void) port;
}

void Dummy_Gpio1Callback(void* port)
{
    (void) port;
}

MotorLibraryStatus_t Dummy_UpdateConfiguration(MotorPort_t* motorPort, const uint8_t* data, uint8_t size)
{
    (void) motorPort;
    (void) data;
    (void) size;

    return MotorLibraryStatus_Ok;
}

MotorLibraryStatus_t Dummy_CreateDriveRequest(const MotorPort_t* motorPort, const uint8_t* data, uint8_t size, DriveRequest_t* request)
{
    (void) motorPort;
    (void) data;
    (void) size;

    *request = (DriveRequest_t) {
        .request_type = DriveRequest_RequestType_Power,
        .request.power = 0,
        .speed_limit = 0.0f,
        .power_limit = 0.0f
    };

    return MotorLibraryStatus_Ok;
}

const MotorLibrary_t motor_library_dummy =
{
    .name                = "NotConfigured",
    .Init                = &Dummy_Init,
    .DeInit              = &Dummy_DeInit,
    .Update              = &Dummy_Update,
    .Gpio0Callback       = &Dummy_Gpio0Callback,
    .Gpio1Callback       = &Dummy_Gpio1Callback,
    .UpdateConfiguration = &Dummy_UpdateConfiguration,
    .CreateDriveRequest  = &Dummy_CreateDriveRequest
};

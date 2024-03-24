#ifndef COMPONENT_VERSION_PROVIDER_H_
#define COMPONENT_VERSION_PROVIDER_H_

#ifndef COMPONENT_TYPES_VERSION_PROVIDER_H_
#define COMPONENT_TYPES_VERSION_PROVIDER_H_

#include <stdio.h>
#include <stdint.h>

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
    const uint8_t* bytes;
    size_t count;
} ConstByteArray_t;

typedef struct {
    uint8_t* bytes;
    size_t count;
} ByteArray_t;

#endif /* COMPONENT_TYPES_VERSION_PROVIDER_H_ */

Comm_Status_t VersionProvider_GetHardwareVersion_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount);

#endif /* COMPONENT_VERSION_PROVIDER_H_ */

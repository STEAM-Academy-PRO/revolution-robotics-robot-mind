#ifndef COMPONENT_COMM_WRAPPER__VERSION_PROVIDER_H_
#define COMPONENT_COMM_WRAPPER__VERSION_PROVIDER_H_

#ifndef COMPONENT_TYPES_COMM_WRAPPER__VERSION_PROVIDER_H_
#define COMPONENT_TYPES_COMM_WRAPPER__VERSION_PROVIDER_H_

#include <stdint.h>
#include <stdio.h>


typedef struct {
    const uint8_t* bytes;
    size_t count;
} ConstByteArray_t;

typedef struct {
    uint8_t* bytes;
    size_t count;
} ByteArray_t;

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

#endif /* COMPONENT_TYPES_COMM_WRAPPER__VERSION_PROVIDER_H_ */

/* Begin User Code Section: Declarations */

/* End User Code Section: Declarations */

Comm_Status_t CommWrapper_VersionProvider_Run_Command_ReadHardwareVersion_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount);
Comm_Status_t CommWrapper_VersionProvider_Run_Command_ReadFirmwareVersion_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount);
ByteArray_t CommWrapper_VersionProvider_Read_FirmwareVersionString(void);
uint32_t CommWrapper_VersionProvider_Read_HardwareVersion(void);

#endif /* COMPONENT_COMM_WRAPPER__VERSION_PROVIDER_H_ */

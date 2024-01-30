#ifndef COMPONENT_VERSION_PROVIDER_H_
#define COMPONENT_VERSION_PROVIDER_H_

#ifndef COMPONENT_TYPES_VERSION_PROVIDER_H_
#define COMPONENT_TYPES_VERSION_PROVIDER_H_

#include <stdint.h>
#include <stdio.h>


typedef struct {
    uint8_t* bytes;
    size_t count;
} ByteArray_t;

#endif /* COMPONENT_TYPES_VERSION_PROVIDER_H_ */

/* Begin User Code Section: Declarations */

/* End User Code Section: Declarations */

uint32_t VersionProvider_Constant_FirmwareVersion(void);
ByteArray_t VersionProvider_Constant_FirmwareVersionString(void);
uint32_t VersionProvider_Constant_HardwareVersion(void);

#endif /* COMPONENT_VERSION_PROVIDER_H_ */

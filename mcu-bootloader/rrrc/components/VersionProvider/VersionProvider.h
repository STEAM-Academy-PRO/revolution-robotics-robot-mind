#ifndef COMPONENT_VERSION_PROVIDER_H_
#define COMPONENT_VERSION_PROVIDER_H_

#include <stdint.h>
#include <stdbool.h>
#include "../MasterCommunication/CommunicationManager.h"

Comm_Status_t VersionProvider_GetHardwareVersion_Start(const uint8_t* commandPayload, uint8_t commandSize, uint8_t* response, uint8_t responseBufferSize, uint8_t* responseCount);

#endif /* COMPONENT_VERSION_PROVIDER_H_ */

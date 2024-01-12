#ifndef COMPONENT_MASTER_COMMUNICATION_INTERFACE_H_
#define COMPONENT_MASTER_COMMUNICATION_INTERFACE_H_

#ifndef COMPONENT_TYPES_MASTER_COMMUNICATION_INTERFACE_H_
#define COMPONENT_TYPES_MASTER_COMMUNICATION_INTERFACE_H_

#include "components/ErrorStorage/ErrorStorageTypes.h"
#include <stdint.h>
#include <stdio.h>


typedef struct {
    const uint8_t* bytes;
    size_t count;
} ConstByteArray_t;

typedef struct {
    ConstByteArray_t default_response;
    ConstByteArray_t rx_overflow_response;
    uint32_t rx_timeout;
} MasterCommunicationInterface_Config_t;

#endif /* COMPONENT_TYPES_MASTER_COMMUNICATION_INTERFACE_H_ */

void MasterCommunicationInterface_Run_OnInit(void);
void MasterCommunicationInterface_Run_SetResponse(ConstByteArray_t response);
void MasterCommunicationInterface_RaiseEvent_RxTimeout(void);
void MasterCommunicationInterface_RaiseEvent_OnMessageReceived(ConstByteArray_t message);
void MasterCommunicationInterface_RaiseEvent_OnTransmissionComplete(void);
void MasterCommunicationInterface_Call_LogError(const ErrorInfo_t* data);
void MasterCommunicationInterface_Read_Configuration(MasterCommunicationInterface_Config_t* value);
uint8_t MasterCommunicationInterface_Read_DeviceAddress(void);

#endif /* COMPONENT_MASTER_COMMUNICATION_INTERFACE_H_ */

#ifndef MASTER_COMMUNICATION_INTERFACE_H_
#define MASTER_COMMUNICATION_INTERFACE_H_

#ifndef COMPONENT_TYPES_MASTER_COMMUNICATION_INTERFACE_H_
#define COMPONENT_TYPES_MASTER_COMMUNICATION_INTERFACE_H_

#include <stdio.h>
#include <stdint.h>

typedef struct {
    const uint8_t* bytes;
    size_t count;
} ConstByteArray_t;

typedef struct
{
    ConstByteArray_t default_response;
    ConstByteArray_t rx_overflow_response;
} MasterCommunicationInterface_Config_t;

#endif /* COMPONENT_TYPES_MASTER_COMMUNICATION_INTERFACE_H_ */

void MasterCommunicationInterface_Run_OnInit(const MasterCommunicationInterface_Config_t* config);
void MasterCommunicationInterface_Run_Update(void);
void MasterCommunicationInterface_Run_SetResponse(ConstByteArray_t response);

void MasterCommunicationInterface_RaiseEvent_OnMessageReceived(ConstByteArray_t message);
void MasterCommunicationInterface_Call_OnTransmitComplete(void);

#endif /* MASTER_COMMUNICATION_INTERFACE_H_ */

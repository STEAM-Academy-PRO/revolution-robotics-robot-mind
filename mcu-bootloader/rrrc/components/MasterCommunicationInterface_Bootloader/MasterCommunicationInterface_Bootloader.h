#ifndef COMPONENT_MASTER_COMMUNICATION_INTERFACE__BOOTLOADER_H_
#define COMPONENT_MASTER_COMMUNICATION_INTERFACE__BOOTLOADER_H_

#ifndef COMPONENT_TYPES_MASTER_COMMUNICATION_INTERFACE__BOOTLOADER_H_
#define COMPONENT_TYPES_MASTER_COMMUNICATION_INTERFACE__BOOTLOADER_H_

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

#endif /* COMPONENT_TYPES_MASTER_COMMUNICATION_INTERFACE__BOOTLOADER_H_ */

/* Begin User Code Section: Declarations */

/* End User Code Section: Declarations */

void MasterCommunicationInterface_Bootloader_Run_OnInit(void);
void MasterCommunicationInterface_Bootloader_Run_Update(void);
void MasterCommunicationInterface_Bootloader_Run_SetResponse(ConstByteArray_t response);
void MasterCommunicationInterface_Bootloader_RaiseEvent_RxTimeout(void);
void MasterCommunicationInterface_Bootloader_RaiseEvent_OnMessageReceived(ConstByteArray_t message);
void MasterCommunicationInterface_Bootloader_RaiseEvent_OnTransmissionComplete(void);
void MasterCommunicationInterface_Bootloader_Read_Configuration(MasterCommunicationInterface_Config_t* value);

#endif /* COMPONENT_MASTER_COMMUNICATION_INTERFACE__BOOTLOADER_H_ */

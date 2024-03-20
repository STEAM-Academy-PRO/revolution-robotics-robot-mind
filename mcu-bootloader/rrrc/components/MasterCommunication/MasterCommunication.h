#ifndef MASTER_COMMUNICATION_H_
#define MASTER_COMMUNICATION_H_

#include "CommunicationManager.h"

void MasterCommunication_Run_OnInit();
void MasterCommunication_Run_HandleCommand(const uint8_t* buffer, size_t bufferSize);

void MasterCommunication_Run_GetDefaultResponse(uint8_t** defaultResponseBuffer, size_t* defaultResponseLength);
void MasterCommunication_Run_GetLongRxErrorResponse(uint8_t** longRxErrorResponseBuffer, size_t* longRxErrorResponseLength);

void MasterCommunication_Call_SendResponse(const uint8_t* responseBuffer, size_t responseSize);

#endif /* MASTER_COMMUNICATION_H_ */

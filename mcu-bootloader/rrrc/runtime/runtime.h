#ifndef RUNTIME_H_
#define RUNTIME_H_

#include "rrrc/components/UpdateManager/UpdateManager.h"
#include "rrrc/components/MasterCommunication/MasterCommunication.h"
#include "rrrc/components/MasterCommunicationInterface/MasterCommunicationInterface.h"
#include "rrrc/components/LEDController/LEDController.h"
#include "rrrc/components/VersionProvider/VersionProvider.h"

#define COMM_HANDLER_COUNT  ((uint8_t) 11u)
extern const Comm_CommandHandler_t communicationHandlers[COMM_HANDLER_COUNT];

void Runtime_RequestJumpToApplication(void);

#endif /* RUNTIME_H_ */

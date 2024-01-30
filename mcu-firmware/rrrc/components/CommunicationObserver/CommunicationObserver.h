#ifndef COMPONENT_COMMUNICATION_OBSERVER_H_
#define COMPONENT_COMMUNICATION_OBSERVER_H_

#ifndef COMPONENT_TYPES_COMMUNICATION_OBSERVER_H_
#define COMPONENT_TYPES_COMMUNICATION_OBSERVER_H_

#include <stdbool.h>


#endif /* COMPONENT_TYPES_COMMUNICATION_OBSERVER_H_ */

/* Begin User Code Section: Declarations */

/* End User Code Section: Declarations */

void CommunicationObserver_Run_OnInit(void);
void CommunicationObserver_Run_OnMessageMissed(void);
void CommunicationObserver_Run_OnMessageReceived(void);
void CommunicationObserver_RaiseEvent_ErrorLimitReached(void);
void CommunicationObserver_RaiseEvent_FirstMessageReceived(void);
bool CommunicationObserver_Read_IsEnabled(void);

#endif /* COMPONENT_COMMUNICATION_OBSERVER_H_ */

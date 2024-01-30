#ifndef RRRC_WORKLOGIC_H_
#define RRRC_WORKLOGIC_H_

#include <stdint.h>
#include "generated_runtime.h"

void RRRC_ProcessLogic_Init(void);
void RRRC_ProcessLogic_xTask(void* user_data);

#define COMM_HANDLER_COUNT  ((uint8_t) 0x42u)
extern const Comm_CommandHandler_t communicationHandlers[COMM_HANDLER_COUNT];

#endif /* RRRC_WORKLOGIC_H_ */


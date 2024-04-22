#ifndef RRRC_WORKLOGIC_H_
#define RRRC_WORKLOGIC_H_

#include <stdint.h>
#include "generated_runtime.h"
#include "runtime/comm_handlers.h"

void RRRC_ProcessLogic_Init(void);
void RRRC_ProcessLogic_xTask(void* user_data);

#endif /* RRRC_WORKLOGIC_H_ */


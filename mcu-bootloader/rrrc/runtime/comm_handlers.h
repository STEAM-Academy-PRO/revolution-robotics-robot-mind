#ifndef RRRC_COMM_HANDLERS_H_
#define RRRC_COMM_HANDLERS_H_

#include <stdint.h>

#define COMM_HANDLER_COUNT  ((uint8_t) 11u)
extern Comm_CommandHandler_t communicationHandlers[COMM_HANDLER_COUNT];

#endif /* RRRC_COMM_HANDLERS_H_ */


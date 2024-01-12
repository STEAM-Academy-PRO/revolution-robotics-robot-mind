#ifndef SCENARIO_HANDLERS_H_
#define SCENARIO_HANDLERS_H_

#include "../RingLedDisplay_private.h"

typedef void (*ledRingFn)(void* data);

typedef struct
{
    ledRingFn init;
    ledRingFn handler;
    ledRingFn DeInit;
    void* userData;
} indication_handler_t;

static const indication_handler_t public_scenario_handlers[8];
static const indication_handler_t startup_indicator_scenario;

#endif /* SCENARIO_HANDLERS_H_ */
#ifndef SCENARIO_HANDLERS_H_
#define SCENARIO_HANDLERS_H_

#include "../RingLedDisplay_private.h"

typedef void (*ledRingFn)(void* data);

typedef struct
{
    const char* name;
    ledRingFn init;
    ledRingFn update;
    ledRingFn uninit;
    void* userData;
} indication_handler_t;

extern const indication_handler_t public_scenario_handlers[9];
extern const indication_handler_t startup_indicator_scenario;

#endif /* SCENARIO_HANDLERS_H_ */
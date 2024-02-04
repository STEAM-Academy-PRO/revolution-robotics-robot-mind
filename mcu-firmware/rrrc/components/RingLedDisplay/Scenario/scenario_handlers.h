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

extern const uint8_t ledLightEffectCount;

const indication_handler_t public_scenario_handlers[];
extern const indication_handler_t startup_indicator_scenario;

#endif /* SCENARIO_HANDLERS_H_ */
#ifndef SERCOM_H_
#define SERCOM_H_

#include <stdint.h>
#include <compiler.h>
#include <hri_sercom_d51.h>
#include "utils.h"
#include "utils_assert.h"

/* Handle SERCOM ownership and interrupt request dispatching */

typedef enum {
    SercomResult_Ok,
    SercomResult_InvalidHw,     /**< hw parameter is not a valid SERCOM instance */
    SercomResult_OwnerError,    /**< owner parameter is not the current owner of the SERCOM instance */
    SercomResult_InvalidHandlerId
} SercomResult_t;

typedef void (*SercomInterruptHandler_t)(void* owner);

typedef struct {
    const uint8_t id;
    void* const hw;
    void* owner;
    SercomInterruptHandler_t interruptHandlers[4];
} SercomInstance_t;

SercomResult_t sercom_init(void* hw, void* owner);
SercomResult_t sercom_set_interrupt_handler(void* owner, uint8_t id, SercomInterruptHandler_t handler);
SercomResult_t sercom_deinit(void* owner);

#endif /* SERCOM_H_ */

#include "sercom_base.h"
#include <stdio.h>

#include <compiler.h>

#define SERCOM_INIT(__sercom_id__) {                \
    .id = __sercom_id__,                            \
    .hw = SERCOM ## __sercom_id__,                  \
    .owner = NULL,                                  \
    .interruptHandlers = { NULL, NULL, NULL, NULL } \
}

static SercomInstance_t instances[4] = {
    SERCOM_INIT(0),
    SERCOM_INIT(1),
    SERCOM_INIT(3),
    SERCOM_INIT(6)
};

static void sercom_disable_irq(SercomInstance_t* instance, uint8_t irq)
{
    NVIC_DisableIRQ((IRQn_Type)(SERCOM0_0_IRQn + instance->id * 4u + irq));
    NVIC_ClearPendingIRQ((IRQn_Type)(SERCOM0_0_IRQn + instance->id * 4u + irq));

    instance->interruptHandlers[irq] = NULL;
}

static void sercom_enable_irq(SercomInstance_t* instance, uint8_t irq, SercomInterruptHandler_t handler)
{
    instance->interruptHandlers[irq] = handler;

    NVIC_ClearPendingIRQ((IRQn_Type)(SERCOM0_0_IRQn + instance->id * 4u + irq));
    NVIC_EnableIRQ((IRQn_Type)(SERCOM0_0_IRQn + instance->id * 4u + irq));
}

static SercomInstance_t* sercom_get_instance_for_hw(void* hw)
{
    for (uint32_t i = 0u; i < ARRAY_SIZE(instances); i++)
    {
        if (instances[i].hw == hw)
        {
            return &instances[i];
        }
    }
    return NULL;
}

static SercomInstance_t* sercom_get_instance_for_owner(void* owner)
{
    for (uint32_t i = 0u; i < ARRAY_SIZE(instances); i++)
    {
        if (instances[i].owner == owner)
        {
            return &instances[i];
        }
    }
    return NULL;
}

SercomResult_t sercom_init(void* hw, void* owner)
{
    SercomInstance_t* instance = sercom_get_instance_for_hw(hw);
    if (!instance)
    {
        return SercomResult_InvalidHw;
    }
    
    if (instance->owner && instance->owner != owner)
    {
        return SercomResult_OwnerError;
    }

    sercom_disable_irq(instance, 0u);
    sercom_disable_irq(instance, 1u);
    sercom_disable_irq(instance, 2u);
    sercom_disable_irq(instance, 3u);

    instance->owner = owner;
    
    return SercomResult_Ok;
}

SercomResult_t sercom_set_interrupt_handler(void* owner, uint8_t id, SercomInterruptHandler_t handler)
{
    SercomInstance_t* instance = sercom_get_instance_for_owner(owner);
    if (!instance)
    {
        return SercomResult_OwnerError;
    }
    
    if (id > ARRAY_SIZE(instance->interruptHandlers))
    {
        return SercomResult_InvalidHandlerId;
    }

    if (handler == NULL)
    {
        sercom_disable_irq(instance, id);
    }
    else
    {
        sercom_enable_irq(instance, id, handler);
    }

    return SercomResult_Ok;
}

SercomResult_t sercom_deinit(void* owner)
{
    SercomInstance_t* instance = sercom_get_instance_for_owner(owner);
    if (!instance)
    {
        return SercomResult_OwnerError;
    }
    
    instance->owner = NULL;

    sercom_disable_irq(instance, 0u);
    sercom_disable_irq(instance, 1u);
    sercom_disable_irq(instance, 2u);
    sercom_disable_irq(instance, 3u);

    return SercomResult_Ok;
}

#define INTERRUPT_HANDLER(__inst_id__, __sercom_id__, __handler_id__)                           \
void SERCOM## __sercom_id__ ## _ ## __handler_id__ ##_Handler(void)                             \
{                                                                                               \
    SercomInterruptHandler_t handler = instances[__inst_id__].interruptHandlers[__handler_id__];\
    if (handler)                                                                                \
    {                                                                                           \
        handler(instances[__inst_id__].owner);                                                  \
    }                                                                                           \
}

/* instance 0, sercom 0 */
INTERRUPT_HANDLER(0, 0, 0)
INTERRUPT_HANDLER(0, 0, 1)
INTERRUPT_HANDLER(0, 0, 2)
INTERRUPT_HANDLER(0, 0, 3)

/* instance 1, sercom 1 */
INTERRUPT_HANDLER(1, 1, 0)
INTERRUPT_HANDLER(1, 1, 1)
INTERRUPT_HANDLER(1, 1, 2)
INTERRUPT_HANDLER(1, 1, 3)

/* instance 2, sercom 3 */
INTERRUPT_HANDLER(2, 3, 0)
INTERRUPT_HANDLER(2, 3, 1)
INTERRUPT_HANDLER(2, 3, 2)
INTERRUPT_HANDLER(2, 3, 3)

/* instance 3, sercom 4 */
INTERRUPT_HANDLER(3, 6, 0)
INTERRUPT_HANDLER(3, 6, 1)
INTERRUPT_HANDLER(3, 6, 2)
INTERRUPT_HANDLER(3, 6, 3)

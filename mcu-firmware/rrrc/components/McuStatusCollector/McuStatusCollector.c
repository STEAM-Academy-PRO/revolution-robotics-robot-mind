#include "McuStatusCollector.h"
#include "utils.h"
#include "utils_assert.h"

/* Begin User Code Section: Declarations */
#include <string.h>
#include <stdbool.h>

static uint32_t slots = 0u;
static uint8_t versions[16];
static uint8_t start_at_slot = 0u;

/**
 * Returns whether the slot was read successfully.
 * If this function returns false, the slots contains data that should be read but does not fit
 * into the destination buffer.
 */
static bool _read_slot(uint8_t index, uint8_t* pData, uint8_t bufferSize, uint8_t* slotSize)
{
    static uint8_t buffer[64];

    *slotSize = 0u;
    uint32_t primask = __get_PRIMASK();
    __disable_irq();
    SlotData_t slot = McuStatusCollector_Read_SlotData(index);

    if (slot.version == versions[index] || ((slot.version & 0x80u) != 0u)) // if highest bit is 1, there is no data
    {
        // data did not change since last read
        __set_PRIMASK(primask);
        return true;
    }

    // copy bytes in critical section to avoid corruption - TODO do this after the size checks
    memcpy(buffer, slot.data.bytes, slot.data.count);
    __set_PRIMASK(primask);

    bool slot_fits = true;

    if (slot.data.count != 0u) /* < does this slot have any new data? */
    {
        if (2u + slot.data.count <= bufferSize) /* < enough space for slot data? */
        {
            pData[0u] = index;
            pData[1u] = slot.data.count;

            memcpy(&pData[2u], buffer, slot.data.count);

            *slotSize = 2u + slot.data.count;

            // store last successfully read version
            versions[index] = slot.version;
        }
        else
        {
            slot_fits = false;
        }
    }

    return slot_fits;
}

static bool is_slot_enabled(uint32_t slot)
{
    return (slots & (1u << slot)) != 0u;
}

/* End User Code Section: Declarations */

void McuStatusCollector_Run_Reset(void)
{
    /* Begin User Code Section: Reset:run Start */
    slots = 0u;
    start_at_slot = 0u;
    memset(versions, 0xFFu, sizeof(versions));
    /* End User Code Section: Reset:run Start */
    /* Begin User Code Section: Reset:run End */

    /* End User Code Section: Reset:run End */
}

uint8_t McuStatusCollector_Run_Read(ByteArray_t destination)
{
    /* Begin User Code Section: Read:run Start */
    uint8_t written = 0u;

    uint8_t start_at = start_at_slot;
    bool all_read = true;

    /*
     * We keep a cursor of which slot we need to read next. This ensures that if not every
     * slot fits into the destination buffer, we can continue reading the remaining slots
     * in the next call to this function.
     */
    for (uint32_t i = start_at; i < 32u; i++)
    {
        if (is_slot_enabled(i))
        {
            uint8_t slotSize = 0u;
            if (_read_slot(i, &destination.bytes[written], destination.count - written, &slotSize))
            {
                written += slotSize;
            }
            else
            {
                /* Record which slot didn't fit, so we can start from here next time */
                start_at_slot = i;
                all_read = false;
                break;
            }
        }
    }

    if (all_read)
    {
        /* If we read all slots so far from the end of the list,
         * we can continue from the beginning */
        for (uint32_t i = 0u; i < start_at; i++)
        {
            if (is_slot_enabled(i))
            {
                uint8_t slotSize = 0u;
                if (_read_slot(i, &destination.bytes[written], destination.count - written, &slotSize))
                {
                    written += slotSize;
                }
                else
                {
                    /* Record which slot didn't fit, so we can start from here next time */
                    start_at_slot = i;
                    break;
                }
            }
        }
    }

    /* End User Code Section: Read:run Start */
    /* Begin User Code Section: Read:run End */

    /* We return how many bytes we wrote into the buffer */
    return written;

    /* End User Code Section: Read:run End */
}

void McuStatusCollector_Run_EnableSlot(uint8_t slot)
{
    /* Begin User Code Section: EnableSlot:run Start */
    ASSERT(slot < 16);

    slots |= (1u << slot);
    versions[slot] = 0xFFu;
    /* End User Code Section: EnableSlot:run Start */
    /* Begin User Code Section: EnableSlot:run End */

    /* End User Code Section: EnableSlot:run End */
}

void McuStatusCollector_Run_DisableSlot(uint8_t slot)
{
    /* Begin User Code Section: DisableSlot:run Start */
    ASSERT(slot < 16);

    slots &= ~(1u << slot);
    /* End User Code Section: DisableSlot:run Start */
    /* Begin User Code Section: DisableSlot:run End */

    /* End User Code Section: DisableSlot:run End */
}

__attribute__((weak))
SlotData_t McuStatusCollector_Read_SlotData(uint32_t index)
{
    ASSERT(index < 16);
    /* Begin User Code Section: SlotData:read Start */

    /* End User Code Section: SlotData:read Start */
    /* Begin User Code Section: SlotData:read End */

    /* End User Code Section: SlotData:read End */
    return (SlotData_t) {
        .data    = {
            .bytes = NULL,
            .count = 0u
        },
        .version = 0xFFu
    };
}

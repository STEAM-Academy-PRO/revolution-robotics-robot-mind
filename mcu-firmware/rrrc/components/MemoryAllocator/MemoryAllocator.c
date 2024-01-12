#include "MemoryAllocator.h"
#include "utils.h"

/* Begin User Code Section: Declarations */
#include "FreeRTOS.h"
/* End User Code Section: Declarations */

void* MemoryAllocator_Run_Allocate(size_t size)
{
    /* Begin User Code Section: Allocate:run Start */

    /* End User Code Section: Allocate:run Start */
    /* Begin User Code Section: Allocate:run End */
    return pvPortMalloc(size);
    /* End User Code Section: Allocate:run End */
}

void MemoryAllocator_Run_Free(void** ptr)
{
    /* Begin User Code Section: Free:run Start */
    vPortFree(*ptr);
    *ptr = NULL;
    /* End User Code Section: Free:run Start */
    /* Begin User Code Section: Free:run End */

    /* End User Code Section: Free:run End */
}

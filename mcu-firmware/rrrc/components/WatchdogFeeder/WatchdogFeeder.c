#include "WatchdogFeeder.h"
#include "utils.h"

/* Begin User Code Section: Declarations */
#include <compiler.h>
#include "hri_wdt_d51.h"
/* End User Code Section: Declarations */

void WatchdogFeeder_Run_Feed(void)
{
    /* Begin User Code Section: Feed:run Start */
    hri_wdt_write_CLEAR_reg(WDT, WDT_CLEAR_CLEAR_KEY);
    /* End User Code Section: Feed:run Start */
    /* Begin User Code Section: Feed:run End */

    /* End User Code Section: Feed:run End */
}

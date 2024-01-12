#include "StartupReasonProvider.h"
#include "utils.h"

/* Begin User Code Section: Declarations */
#include <compiler.h>
#include "hri_rstc_d51.h"
/* End User Code Section: Declarations */

void StartupReasonProvider_Run_OnInit(void)
{
    /* Begin User Code Section: OnInit:run Start */
    if (hri_rstc_get_RCAUSE_POR_bit(RSTC) || hri_rstc_get_RCAUSE_EXT_bit(RSTC))
    {
        // we currntly don't use the external reset pin, but with some probability it is fired during startup
        StartupReasonProvider_Write_IsColdStart(true);
    }
    else
    {
        StartupReasonProvider_Write_IsColdStart(false);
    }
    /* End User Code Section: OnInit:run Start */
    /* Begin User Code Section: OnInit:run End */

    /* End User Code Section: OnInit:run End */
}

__attribute__((weak))
void StartupReasonProvider_Write_IsColdStart(bool value)
{
    (void) value;
    /* Begin User Code Section: IsColdStart:write Start */

    /* End User Code Section: IsColdStart:write Start */
    /* Begin User Code Section: IsColdStart:write End */

    /* End User Code Section: IsColdStart:write End */
}

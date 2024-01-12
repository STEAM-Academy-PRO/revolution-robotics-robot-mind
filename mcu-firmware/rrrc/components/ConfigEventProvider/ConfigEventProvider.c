#include "ConfigEventProvider.h"
#include "utils.h"

/* Begin User Code Section: Declarations */

/* End User Code Section: Declarations */

void ConfigEventProvider_Run_DispatchConfigEvent(void)
{
    /* Begin User Code Section: DispatchConfigEvent:run Start */
    ConfigEventProvider_RaiseEvent_OnConfigEventReceived();
    /* End User Code Section: DispatchConfigEvent:run Start */
    /* Begin User Code Section: DispatchConfigEvent:run End */

    /* End User Code Section: DispatchConfigEvent:run End */
}

__attribute__((weak))
void ConfigEventProvider_RaiseEvent_OnConfigEventReceived(void)
{
    /* Begin User Code Section: OnConfigEventReceived:run Start */

    /* End User Code Section: OnConfigEventReceived:run Start */
    /* Begin User Code Section: OnConfigEventReceived:run End */

    /* End User Code Section: OnConfigEventReceived:run End */
}

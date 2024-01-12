#include "HardwareCompatibilityChecker.h"
#include "utils.h"

/* Begin User Code Section: Declarations */
#include <stdbool.h>
#include <stdio.h>
/* End User Code Section: Declarations */

void HardwareCompatibilityChecker_Run_OnInit(void)
{
    /* Begin User Code Section: OnInit:run Start */
    {
        const uint32_t compatible_hw[] = { COMPATIBLE_HW_VERSIONS };
        const uint32_t hw = HardwareCompatibilityChecker_Read_HardwareVersion();
        bool on_compatible_hw = false;
        for (size_t i = 0u; i < ARRAY_SIZE(compatible_hw); i++)
        {
            if (hw == compatible_hw[i])
            {
                on_compatible_hw = true;
                break;
            }
        }

        if (!on_compatible_hw)
        {
            HardwareCompatibilityChecker_RaiseEvent_OnIncompatibleHardware();
        }
    }
    /* End User Code Section: OnInit:run Start */
    /* Begin User Code Section: OnInit:run End */

    /* End User Code Section: OnInit:run End */
}

__attribute__((weak))
void HardwareCompatibilityChecker_RaiseEvent_OnIncompatibleHardware(void)
{
    /* Begin User Code Section: OnIncompatibleHardware:run Start */

    /* End User Code Section: OnIncompatibleHardware:run Start */
    /* Begin User Code Section: OnIncompatibleHardware:run End */

    /* End User Code Section: OnIncompatibleHardware:run End */
}

__attribute__((weak))
uint32_t HardwareCompatibilityChecker_Read_HardwareVersion(void)
{
    /* Begin User Code Section: HardwareVersion:read Start */

    /* End User Code Section: HardwareVersion:read Start */
    /* Begin User Code Section: HardwareVersion:read End */

    /* End User Code Section: HardwareVersion:read End */
    return 0;
}

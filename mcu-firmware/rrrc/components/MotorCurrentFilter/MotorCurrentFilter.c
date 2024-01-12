#include "MotorCurrentFilter.h"
#include "utils.h"
#include "utils_assert.h"

/* Begin User Code Section: Declarations */
static Current_t motorCurrents[6];
/* End User Code Section: Declarations */

void MotorCurrentFilter_Run_OnInit(void)
{
    /* Begin User Code Section: OnInit:run Start */
    for (uint32_t i = 0u; i < ARRAY_SIZE(motorCurrents); i++)
    {
        motorCurrents[i] = 0.0f;
    }
    /* End User Code Section: OnInit:run Start */
    /* Begin User Code Section: OnInit:run End */

    /* End User Code Section: OnInit:run End */
}

void MotorCurrentFilter_Run_Update(void)
{
    /* Begin User Code Section: Update:run Start */
    for (uint32_t i = 0u; i < ARRAY_SIZE(motorCurrents); i++)
    {
        Current_t prev_current = motorCurrents[i];
        Current_t current = MotorCurrentFilter_Read_RawCurrent(i);

        current = current * 0.05f + prev_current * 0.95f;
        motorCurrents[i] = current;

        MotorCurrentFilter_Write_FilteredCurrent(i, current);
    }
    /* End User Code Section: Update:run Start */
    /* Begin User Code Section: Update:run End */

    /* End User Code Section: Update:run End */
}

__attribute__((weak))
void MotorCurrentFilter_Write_FilteredCurrent(uint32_t index, Current_t value)
{
    (void) value;
    ASSERT(index < 6);
    /* Begin User Code Section: FilteredCurrent:write Start */

    /* End User Code Section: FilteredCurrent:write Start */
    /* Begin User Code Section: FilteredCurrent:write End */

    /* End User Code Section: FilteredCurrent:write End */
}

__attribute__((weak))
Current_t MotorCurrentFilter_Read_RawCurrent(uint32_t index)
{
    ASSERT(index < 6);
    /* Begin User Code Section: RawCurrent:read Start */

    /* End User Code Section: RawCurrent:read Start */
    /* Begin User Code Section: RawCurrent:read End */

    /* End User Code Section: RawCurrent:read End */
    return 0.0f;
}

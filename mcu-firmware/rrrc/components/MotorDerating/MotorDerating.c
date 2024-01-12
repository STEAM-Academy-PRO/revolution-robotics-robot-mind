#include "MotorDerating.h"
#include "utils.h"
#include "utils_assert.h"

/* Begin User Code Section: Declarations */
#include <math.h>
#include "utils/functions.h"
/* End User Code Section: Declarations */

void MotorDerating_Run_OnUpdate(void)
{
    /* Begin User Code Section: OnUpdate:run Start */
    MotorDeratingParameters_t params;
    MotorDerating_Read_Parameters(&params);

    for (uint32_t motor_idx = 0u; motor_idx < 6u; motor_idx++)
    {
        int16_t control = MotorDerating_Read_ControlValue(motor_idx);

        Current_t maxCurrent = MotorDerating_Read_MaxMotorCurrent(motor_idx);
        Current_t current = MotorDerating_Read_MotorCurrent(motor_idx);

        float current_limiting = 1.0f;
        if (maxCurrent != 0.0f)
        {
            if (current > maxCurrent)
            {
                current_limiting = maxCurrent / current;
            }
            MotorDerating_Write_RelativeMotorCurrent(motor_idx, 100.0f * current / maxCurrent);
        }
        else
        {
            MotorDerating_Write_RelativeMotorCurrent(motor_idx, 0.0f);
        }

        Temperature_t temp = MotorDerating_Read_MotorTemperature(motor_idx);
        float temperature_limiting = map_constrained(temp, params.MaxSafeTemperature, params.MaxAllowedTemperature, 1, 0);

        float derating_ratio = min(temperature_limiting, current_limiting);
        float derated = derating_ratio * control;

        MotorDerating_Write_MaxPowerRatio(motor_idx, derating_ratio);
        MotorDerating_Write_DeratedControlValue(motor_idx, (int16_t)lroundf(derated));
    }
    /* End User Code Section: OnUpdate:run Start */
    /* Begin User Code Section: OnUpdate:run End */

    /* End User Code Section: OnUpdate:run End */
}

__attribute__((weak))
void MotorDerating_Write_DeratedControlValue(uint32_t index, int16_t value)
{
    (void) value;
    ASSERT(index < 6);
    /* Begin User Code Section: DeratedControlValue:write Start */

    /* End User Code Section: DeratedControlValue:write Start */
    /* Begin User Code Section: DeratedControlValue:write End */

    /* End User Code Section: DeratedControlValue:write End */
}

__attribute__((weak))
void MotorDerating_Write_MaxPowerRatio(uint32_t index, Percentage_t value)
{
    (void) value;
    ASSERT(index < 6);
    /* Begin User Code Section: MaxPowerRatio:write Start */

    /* End User Code Section: MaxPowerRatio:write Start */
    /* Begin User Code Section: MaxPowerRatio:write End */

    /* End User Code Section: MaxPowerRatio:write End */
}

__attribute__((weak))
void MotorDerating_Write_RelativeMotorCurrent(uint32_t index, Percentage_t value)
{
    (void) value;
    ASSERT(index < 6);
    /* Begin User Code Section: RelativeMotorCurrent:write Start */

    /* End User Code Section: RelativeMotorCurrent:write Start */
    /* Begin User Code Section: RelativeMotorCurrent:write End */

    /* End User Code Section: RelativeMotorCurrent:write End */
}

__attribute__((weak))
int16_t MotorDerating_Read_ControlValue(uint32_t index)
{
    ASSERT(index < 6);
    /* Begin User Code Section: ControlValue:read Start */

    /* End User Code Section: ControlValue:read Start */
    /* Begin User Code Section: ControlValue:read End */

    /* End User Code Section: ControlValue:read End */
    return 0;
}

__attribute__((weak))
Current_t MotorDerating_Read_MaxMotorCurrent(uint32_t index)
{
    ASSERT(index < 6);
    /* Begin User Code Section: MaxMotorCurrent:read Start */

    /* End User Code Section: MaxMotorCurrent:read Start */
    /* Begin User Code Section: MaxMotorCurrent:read End */

    /* End User Code Section: MaxMotorCurrent:read End */
    return (Current_t) 0.0f;
}

__attribute__((weak))
Current_t MotorDerating_Read_MotorCurrent(uint32_t index)
{
    ASSERT(index < 6);
    /* Begin User Code Section: MotorCurrent:read Start */

    /* End User Code Section: MotorCurrent:read Start */
    /* Begin User Code Section: MotorCurrent:read End */

    /* End User Code Section: MotorCurrent:read End */
    return (Current_t) 0.0f;
}

__attribute__((weak))
Temperature_t MotorDerating_Read_MotorTemperature(uint32_t index)
{
    ASSERT(index < 6);
    /* Begin User Code Section: MotorTemperature:read Start */

    /* End User Code Section: MotorTemperature:read Start */
    /* Begin User Code Section: MotorTemperature:read End */

    /* End User Code Section: MotorTemperature:read End */
    return (Temperature_t) 20.0f;
}

__attribute__((weak))
void MotorDerating_Read_Parameters(MotorDeratingParameters_t* value)
{
    ASSERT(value != NULL);
    /* Begin User Code Section: Parameters:read Start */

    /* End User Code Section: Parameters:read Start */
    *value = (MotorDeratingParameters_t) {
        .MaxSafeTemperature    = 0.0f,
        .MaxAllowedTemperature = 0.0f
    };
    /* Begin User Code Section: Parameters:read End */

    /* End User Code Section: Parameters:read End */
}

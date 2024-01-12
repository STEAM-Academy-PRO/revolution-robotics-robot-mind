#include "BatteryCharger.h"
#include "utils.h"

/* Begin User Code Section: Declarations */
#include "rrrc_hal.h"

#include <stdbool.h>

#define ERROR_INCREMENT (20u)
#define MAX_ERROR_COUNT (220u)
#define ERROR_THRESHOLD (100u)

static ChargerState_t previousChargerState;
static uint8_t errorScore;

static ChargerState_t get_charger_state( void )
{
    bool isCharging = gpio_get_pin_level(CHARGER_STAT) == 0u;
    bool isCharged = gpio_get_pin_level(CHARGER_STBY) == 0u;

    if (isCharging)
    {
        return ChargerState_Charging;
    }
    else
    {
        if (isCharged)
        {
            return ChargerState_Charged;
        }
        else
        {
            return ChargerState_NotPluggedIn;
        }
    }
}
/* End User Code Section: Declarations */

void BatteryCharger_Run_OnInit(void)
{
    /* Begin User Code Section: OnInit:run Start */
    gpio_set_pin_direction(CHARGER_STBY, GPIO_DIRECTION_IN);
    gpio_set_pin_pull_mode(CHARGER_STBY, GPIO_PULL_UP);
    gpio_set_pin_function(CHARGER_STBY, GPIO_PIN_FUNCTION_OFF);

    gpio_set_pin_direction(CHARGER_STAT, GPIO_DIRECTION_IN);
    gpio_set_pin_pull_mode(CHARGER_STAT, GPIO_PULL_UP);
    gpio_set_pin_function(CHARGER_STAT, GPIO_PIN_FUNCTION_OFF);

    errorScore = 0u;

    previousChargerState = get_charger_state();
    /* End User Code Section: OnInit:run Start */
    /* Begin User Code Section: OnInit:run End */

    /* End User Code Section: OnInit:run End */
}

void BatteryCharger_Run_Update(void)
{
    /* Begin User Code Section: Update:run Start */
    ChargerState_t state = get_charger_state();

    if (state != previousChargerState)
    {
        if (errorScore < MAX_ERROR_COUNT)
        {
            errorScore += ERROR_INCREMENT;
        }
    }
    else if (errorScore > 0u)
    {
        --errorScore;
    }
    previousChargerState = state;

    if (errorScore > ERROR_THRESHOLD)
    {
        BatteryCharger_Write_ChargerState(ChargerState_Fault);
    }
    else
    {
        BatteryCharger_Write_ChargerState(state);
    }
    /* End User Code Section: Update:run Start */
    /* Begin User Code Section: Update:run End */

    /* End User Code Section: Update:run End */
}

__attribute__((weak))
void BatteryCharger_Write_ChargerState(ChargerState_t value)
{
    (void) value;
    /* Begin User Code Section: ChargerState:write Start */

    /* End User Code Section: ChargerState:write Start */
    /* Begin User Code Section: ChargerState:write End */

    /* End User Code Section: ChargerState:write End */
}

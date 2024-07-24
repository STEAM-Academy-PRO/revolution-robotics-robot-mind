#include "PowerSwitch.h"
#include "utils.h"

/* Begin User Code Section: Declarations */
#include "rrrc_hal.h"
#include "CommonLibraries/log.h"

#ifdef DEBUG_LOG
static bool previous_state = false;
#endif
/* End User Code Section: Declarations */

void PowerSwitch_Run_OnInit(void)
{
    /* Begin User Code Section: OnInit:run Start */
    gpio_set_pin_direction(PWR_EN, GPIO_DIRECTION_IN);
    gpio_set_pin_pull_mode(PWR_EN, GPIO_PULL_UP);
    gpio_set_pin_function(PWR_EN, GPIO_PIN_FUNCTION_OFF);

    /* End User Code Section: OnInit:run Start */
    /* Begin User Code Section: OnInit:run End */

    /* End User Code Section: OnInit:run End */
}

void PowerSwitch_Run_Update(void)
{
    /* Begin User Code Section: Update:run Start */

    /*
    PWR_EN is VBAT_SW after an inverting MOSFET. If the switch is on, VBAT_SW is at
    some high level, which pulls PWR_EN low.
    */
    bool isOn = gpio_get_pin_level(PWR_EN) == 0u;

    #ifdef DEBUG_LOG
    if (isOn != previous_state)
    {
        previous_state = isOn;
        LOG("PowerSwitch: %s", isOn ? "ON" : "OFF");
    }
    #endif

    PowerSwitch_Write_IsSwitchedOn(isOn);

    /* End User Code Section: Update:run Start */
    /* Begin User Code Section: Update:run End */

    /* End User Code Section: Update:run End */
}

__attribute__((weak))
void PowerSwitch_Write_IsSwitchedOn(bool value)
{
    (void) value;
    /* Begin User Code Section: IsSwitchedOn:write Start */

    /* End User Code Section: IsSwitchedOn:write Start */
    /* Begin User Code Section: IsSwitchedOn:write End */

    /* End User Code Section: IsSwitchedOn:write End */
}

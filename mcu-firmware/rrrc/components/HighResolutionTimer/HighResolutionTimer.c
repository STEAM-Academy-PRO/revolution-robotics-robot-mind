#include "HighResolutionTimer.h"
#include "utils.h"

/* Begin User Code Section: Declarations */
#include "driver_init.h"
#include <peripheral_clk_config.h>
/* End User Code Section: Declarations */

void HighResolutionTimer_Run_OnInit(void)
{
    /* Begin User Code Section: OnInit:run Start */
    hri_mclk_set_APBDMASK_TC6_bit(MCLK);
    hri_mclk_set_APBDMASK_TC7_bit(MCLK);
    hri_gclk_write_PCHCTRL_reg(GCLK, TC6_GCLK_ID, CONF_GCLK_TC6_SRC | (1 << GCLK_PCHCTRL_CHEN_Pos));
    hri_gclk_write_PCHCTRL_reg(GCLK, TC7_GCLK_ID, CONF_GCLK_TC7_SRC | (1 << GCLK_PCHCTRL_CHEN_Pos));

    struct _timer_device tc6_device;

    _tc_timer_init(&tc6_device, TC6);
    _tc_timer_start(&tc6_device);
    /* End User Code Section: OnInit:run Start */
    /* Begin User Code Section: OnInit:run End */

    /* End User Code Section: OnInit:run End */
}

uint32_t HighResolutionTimer_Run_GetTickCount(void)
{
    /* Begin User Code Section: GetTickCount:run Start */
    hri_tc_set_CTRLB_CMD_bf(TC6, TC_CTRLBSET_CMD_READSYNC_Val);
    while (hri_tc_read_CTRLB_CMD_bf(TC6) != 0u);

    return hri_tccount32_get_COUNT_COUNT_bf(TC6, 0xFFFFFFFFu);
    /* End User Code Section: GetTickCount:run Start */
    /* Begin User Code Section: GetTickCount:run End */

    /* End User Code Section: GetTickCount:run End */
}

float HighResolutionTimer_Run_ToMs(uint32_t ticks)
{
    /* Begin User Code Section: ToMs:run Start */
    return ticks / 24.0f;
    /* End User Code Section: ToMs:run Start */
    /* Begin User Code Section: ToMs:run End */

    /* End User Code Section: ToMs:run End */
}

uint32_t HighResolutionTimer_Constant_TicksInMs(void)
{
    /* Begin User Code Section: TicksInMs:constant Start */

    /* End User Code Section: TicksInMs:constant Start */
    /* Begin User Code Section: TicksInMs:constant End */

    /* End User Code Section: TicksInMs:constant End */
    return 24u;
}

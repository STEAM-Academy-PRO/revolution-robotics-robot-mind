#include "RestartManager.h"
#include "utils.h"

/* Begin User Code Section: Declarations */
#include "rrrc_hal.h"

static const void * s_rtc_module = (const void *) RTC;
/* End User Code Section: Declarations */

void RestartManager_Run_Reset(void)
{
    /* Begin User Code Section: Reset:run Start */
    NVIC_SystemReset();
    /* End User Code Section: Reset:run Start */
    /* Begin User Code Section: Reset:run End */

    /* End User Code Section: Reset:run End */
}

void RestartManager_Run_RebootToBootloader(void)
{
    /* Begin User Code Section: RebootToBootloader:run Start */
    hri_rtcmode0_set_CTRLB_GP0EN_bit(s_rtc_module);
    hri_rtcmode0_set_CTRLB_GP2EN_bit(s_rtc_module);

    hri_rtc_write_GP_reg(s_rtc_module, 0u, (hri_rtc_gp_reg_t) 0xFFFFFFFFu);
    hri_rtc_write_GP_reg(s_rtc_module, 1u, (hri_rtc_gp_reg_t) 0xFFFFFFFFu);
    hri_rtc_write_GP_reg(s_rtc_module, 2u, (hri_rtc_gp_reg_t) 0xFFFFFFFFu);
    hri_rtc_write_GP_reg(s_rtc_module, 3u, (hri_rtc_gp_reg_t) 0xFFFFFFFFu);

    NVIC_SystemReset();
    /* End User Code Section: RebootToBootloader:run Start */
    /* Begin User Code Section: RebootToBootloader:run End */

    /* End User Code Section: RebootToBootloader:run End */
}

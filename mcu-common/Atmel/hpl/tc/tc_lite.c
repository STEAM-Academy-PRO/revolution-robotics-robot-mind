
/**
 * \file
 *
 * \brief TC related functionality implementation.
 *
 * Copyright (c) 2017 Microchip Technology Inc. and its subsidiaries.
 *
 * \asf_license_start
 *
 * \page License
 *
 * Subject to your compliance with these terms, you may use Microchip
 * software and any derivatives exclusively with Microchip products.
 * It is your responsibility to comply with third party license terms applicable
 * to your use of third party software (including open source software) that
 * may accompany Microchip software.
 *
 * THIS SOFTWARE IS SUPPLIED BY MICROCHIP "AS IS". NO WARRANTIES,
 * WHETHER EXPRESS, IMPLIED OR STATUTORY, APPLY TO THIS SOFTWARE,
 * INCLUDING ANY IMPLIED WARRANTIES OF NON-INFRINGEMENT, MERCHANTABILITY,
 * AND FITNESS FOR A PARTICULAR PURPOSE. IN NO EVENT WILL MICROCHIP BE
 * LIABLE FOR ANY INDIRECT, SPECIAL, PUNITIVE, INCIDENTAL OR CONSEQUENTIAL
 * LOSS, DAMAGE, COST OR EXPENSE OF ANY KIND WHATSOEVER RELATED TO THE
 * SOFTWARE, HOWEVER CAUSED, EVEN IF MICROCHIP HAS BEEN ADVISED OF THE
 * POSSIBILITY OR THE DAMAGES ARE FORESEEABLE.  TO THE FULLEST EXTENT
 * ALLOWED BY LAW, MICROCHIP'S TOTAL LIABILITY ON ALL CLAIMS IN ANY WAY
 * RELATED TO THIS SOFTWARE WILL NOT EXCEED THE AMOUNT OF FEES, IF ANY,
 * THAT YOU HAVE PAID DIRECTLY TO MICROCHIP FOR THIS SOFTWARE.
 *
 * \asf_license_stop
 *
 */

#include "tc_lite.h"

/* setup function for NPWM timers */
static inline int8_t TIMER_any_init(Tc* timer)
{
    if (!hri_tc_is_syncing(timer, TC_SYNCBUSY_SWRST)) {
        if (hri_tc_get_CTRLA_reg(timer, TC_CTRLA_ENABLE)) {
            hri_tc_clear_CTRLA_ENABLE_bit(timer);
            hri_tc_wait_for_sync(timer, TC_SYNCBUSY_ENABLE);
        }
        hri_tc_write_CTRLA_reg(timer, TC_CTRLA_SWRST);
    }
    hri_tc_wait_for_sync(timer, TC_SYNCBUSY_SWRST);

    hri_tc_write_CTRLA_reg(timer, TC_CTRLA_MODE_COUNT8 | TC_CTRLA_PRESCALER_DIV4);
    hri_tc_write_CTRLB_reg(timer,
                           0 << TC_CTRLBSET_CMD_Pos
                               | 0 << TC_CTRLBSET_ONESHOT_Pos
                               | 0 << TC_CTRLBCLR_LUPD_Pos
                               | 0 << TC_CTRLBSET_DIR_Pos);

    hri_tc_write_EVCTRL_reg(timer,
                           1 << TC_EVCTRL_TCEI_Pos
                           | TC_EVCTRL_OVFEO
                           | TC_EVCTRL_EVACT_RETRIGGER);

    hri_tc_write_WAVE_reg(timer, 2);
    hri_tc_write_CTRLA_ENABLE_bit(timer, 1 << TC_CTRLA_ENABLE_Pos);

    return 0;
}

int8_t TIMER_0_init(void)
{
    return TIMER_any_init(TC0);
}

int8_t TIMER_1_init(void)
{
    return TIMER_any_init(TC1);
}

int8_t TIMER_2_init(void)
{
    return TIMER_any_init(TC2);
}

int8_t TIMER_3_init(void)
{
    return TIMER_any_init(TC3);
}

int8_t TIMER_4_init(void)
{
    return TIMER_any_init(TC4);
}

int8_t TIMER_5_init(void)
{
    return TIMER_any_init(TC5);
}

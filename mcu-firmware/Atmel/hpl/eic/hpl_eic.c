
/**
 * \file
 *
 * \brief EIC related functionality implementation.
 *
 * Copyright (c) 2015-2018 Microchip Technology Inc. and its subsidiaries.
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
#include <compiler.h>
#include <hpl_eic_config.h>
#include <hpl_ext_irq.h>
#include <string.h>
#include <utils.h>
#include <utils_assert.h>

#ifndef CONFIG_EIC_EXTINT_MAP
/** Dummy mapping to pass compiling. */
#define INVALID_PIN_NUMBER      0xFFFFFFFFu
#define CONFIG_EIC_EXTINT_MAP                                                                   \
    {                                                                                           \
        INVALID_PIN_NUMBER,                                                                     \
        INVALID_PIN_NUMBER,                                                                     \
        INVALID_PIN_NUMBER,                                                                     \
        INVALID_PIN_NUMBER,                                                                     \
        INVALID_PIN_NUMBER,                                                                     \
        INVALID_PIN_NUMBER,                                                                     \
        INVALID_PIN_NUMBER,                                                                     \
        INVALID_PIN_NUMBER,                                                                     \
        INVALID_PIN_NUMBER,                                                                     \
        INVALID_PIN_NUMBER,                                                                     \
        INVALID_PIN_NUMBER,                                                                     \
        INVALID_PIN_NUMBER,                                                                     \
        INVALID_PIN_NUMBER,                                                                     \
        INVALID_PIN_NUMBER,                                                                     \
        INVALID_PIN_NUMBER,                                                                     \
        INVALID_PIN_NUMBER                                                                      \
    }
#endif

#define EXT_IRQ_AMOUNT 16

/**
 * \brief PIN and EXTINT map for enabled external interrupts
 */
static const uint32_t _exti_ch_pins[EXT_IRQ_AMOUNT] = CONFIG_EIC_EXTINT_MAP;

/**
 * \brief Callbacks for the individual channels
 */
typedef struct {
    ext_irq_cb_t callback;
    void* data;
} exti_t;

static exti_t extis[EXT_IRQ_AMOUNT];

/**
 * \brief Initialize external interrupt module
 */
static void NVIC_SetStateIRQ(IRQn_Type IRQnum, bool enable)
{
    NVIC_DisableIRQ(IRQnum);

    if (enable)
    {
        NVIC_ClearPendingIRQ(IRQnum);
        NVIC_EnableIRQ(IRQnum);
    }
}

void _ext_irq_clear_pending(const uint32_t pin)
{
    uint8_t extint = 0u;

    while (extint < EXT_IRQ_AMOUNT && _exti_ch_pins[extint] != pin)
    {
        extint++;
    }

    if (extint == EXT_IRQ_AMOUNT)
    {
        return;
    }
    hri_eic_clear_INTFLAG_reg(EIC, 1ul << extint);
    NVIC_ClearPendingIRQ(EIC_0_IRQn + extint);
}

int32_t _ext_irq_init(void)
{
    for (uint32_t i = 0u; i < EXT_IRQ_AMOUNT; i++)
    {
        extis[i].callback = NULL;
        extis[i].data = NULL;
    }

    if (!hri_eic_is_syncing(EIC, EIC_SYNCBUSY_SWRST)) {
        if (hri_eic_get_CTRLA_reg(EIC, EIC_CTRLA_ENABLE)) {
            hri_eic_clear_CTRLA_ENABLE_bit(EIC);
            hri_eic_wait_for_sync(EIC, EIC_SYNCBUSY_ENABLE);
        }
        hri_eic_write_CTRLA_reg(EIC, EIC_CTRLA_SWRST);
    }
    hri_eic_wait_for_sync(EIC, EIC_SYNCBUSY_SWRST);

    hri_eic_write_CTRLA_CKSEL_bit(EIC, CONF_EIC_CKSEL);

    hri_eic_write_NMICTRL_reg(EIC,
                              (CONF_EIC_NMIFILTEN << EIC_NMICTRL_NMIFILTEN_Pos)
                                  | EIC_NMICTRL_NMISENSE(CONF_EIC_NMISENSE) | EIC_ASYNCH_ASYNCH(CONF_EIC_NMIASYNCH)
                                  | 0);

    hri_eic_write_EVCTRL_reg(EIC,
                             (CONF_EIC_EXTINTEO0 << 0) | (CONF_EIC_EXTINTEO1 << 1) | (CONF_EIC_EXTINTEO2 << 2)
                                 | (CONF_EIC_EXTINTEO3 << 3) | (CONF_EIC_EXTINTEO4 << 4) | (CONF_EIC_EXTINTEO5 << 5)
                                 | (CONF_EIC_EXTINTEO6 << 6) | (CONF_EIC_EXTINTEO7 << 7) | (CONF_EIC_EXTINTEO8 << 8)
                                 | (CONF_EIC_EXTINTEO9 << 9) | (CONF_EIC_EXTINTEO10 << 10) | (CONF_EIC_EXTINTEO11 << 11)
                                 | (CONF_EIC_EXTINTEO12 << 12) | (CONF_EIC_EXTINTEO13 << 13)
                                 | (CONF_EIC_EXTINTEO14 << 14) | (CONF_EIC_EXTINTEO15 << 15) | 0);
    hri_eic_write_ASYNCH_reg(EIC,
                             (CONF_EIC_ASYNCH0 << 0) | (CONF_EIC_ASYNCH1 << 1) | (CONF_EIC_ASYNCH2 << 2)
                                 | (CONF_EIC_ASYNCH3 << 3) | (CONF_EIC_ASYNCH4 << 4) | (CONF_EIC_ASYNCH5 << 5)
                                 | (CONF_EIC_ASYNCH6 << 6) | (CONF_EIC_ASYNCH7 << 7) | (CONF_EIC_ASYNCH8 << 8)
                                 | (CONF_EIC_ASYNCH9 << 9) | (CONF_EIC_ASYNCH10 << 10) | (CONF_EIC_ASYNCH11 << 11)
                                 | (CONF_EIC_ASYNCH12 << 12) | (CONF_EIC_ASYNCH13 << 13) | (CONF_EIC_ASYNCH14 << 14)
                                 | (CONF_EIC_ASYNCH15 << 15) | 0);
    hri_eic_write_DEBOUNCEN_reg(
        EIC,
        (CONF_EIC_DEBOUNCE_ENABLE0 << 0) | (CONF_EIC_DEBOUNCE_ENABLE1 << 1) | (CONF_EIC_DEBOUNCE_ENABLE2 << 2)
            | (CONF_EIC_DEBOUNCE_ENABLE3 << 3) | (CONF_EIC_DEBOUNCE_ENABLE4 << 4) | (CONF_EIC_DEBOUNCE_ENABLE5 << 5)
            | (CONF_EIC_DEBOUNCE_ENABLE6 << 6) | (CONF_EIC_DEBOUNCE_ENABLE7 << 7) | (CONF_EIC_DEBOUNCE_ENABLE8 << 8)
            | (CONF_EIC_DEBOUNCE_ENABLE9 << 9) | (CONF_EIC_DEBOUNCE_ENABLE10 << 10) | (CONF_EIC_DEBOUNCE_ENABLE11 << 11)
            | (CONF_EIC_DEBOUNCE_ENABLE12 << 12) | (CONF_EIC_DEBOUNCE_ENABLE13 << 13)
            | (CONF_EIC_DEBOUNCE_ENABLE14 << 14) | (CONF_EIC_DEBOUNCE_ENABLE15 << 15) | 0);

    hri_eic_write_DPRESCALER_reg(
        EIC,
        (EIC_DPRESCALER_PRESCALER0(CONF_EIC_DPRESCALER0)) | (CONF_EIC_STATES0 << EIC_DPRESCALER_STATES0_Pos)
            | (EIC_DPRESCALER_PRESCALER1(CONF_EIC_DPRESCALER1)) | (CONF_EIC_STATES1 << EIC_DPRESCALER_STATES1_Pos)
            | CONF_EIC_TICKON << EIC_DPRESCALER_TICKON_Pos | 0);

    hri_eic_write_CONFIG_reg(EIC,
                             0,
                             (CONF_EIC_FILTEN0 << EIC_CONFIG_FILTEN0_Pos) | EIC_CONFIG_SENSE0(CONF_EIC_SENSE0)
                                 | (CONF_EIC_FILTEN1 << EIC_CONFIG_FILTEN1_Pos) | EIC_CONFIG_SENSE1(CONF_EIC_SENSE1)
                                 | (CONF_EIC_FILTEN2 << EIC_CONFIG_FILTEN2_Pos) | EIC_CONFIG_SENSE2(CONF_EIC_SENSE2)
                                 | (CONF_EIC_FILTEN3 << EIC_CONFIG_FILTEN3_Pos) | EIC_CONFIG_SENSE3(CONF_EIC_SENSE3)
                                 | (CONF_EIC_FILTEN4 << EIC_CONFIG_FILTEN4_Pos) | EIC_CONFIG_SENSE4(CONF_EIC_SENSE4)
                                 | (CONF_EIC_FILTEN5 << EIC_CONFIG_FILTEN5_Pos) | EIC_CONFIG_SENSE5(CONF_EIC_SENSE5)
                                 | (CONF_EIC_FILTEN6 << EIC_CONFIG_FILTEN6_Pos) | EIC_CONFIG_SENSE6(CONF_EIC_SENSE6)
                                 | (CONF_EIC_FILTEN7 << EIC_CONFIG_FILTEN7_Pos) | EIC_CONFIG_SENSE7(CONF_EIC_SENSE7)
                                 | 0);

    hri_eic_write_CONFIG_reg(EIC,
                             1,
                             (CONF_EIC_FILTEN8 << EIC_CONFIG_FILTEN0_Pos) | EIC_CONFIG_SENSE0(CONF_EIC_SENSE8)
                                 | (CONF_EIC_FILTEN9 << EIC_CONFIG_FILTEN1_Pos) | EIC_CONFIG_SENSE1(CONF_EIC_SENSE9)
                                 | (CONF_EIC_FILTEN10 << EIC_CONFIG_FILTEN2_Pos) | EIC_CONFIG_SENSE2(CONF_EIC_SENSE10)
                                 | (CONF_EIC_FILTEN11 << EIC_CONFIG_FILTEN3_Pos) | EIC_CONFIG_SENSE3(CONF_EIC_SENSE11)
                                 | (CONF_EIC_FILTEN12 << EIC_CONFIG_FILTEN4_Pos) | EIC_CONFIG_SENSE4(CONF_EIC_SENSE12)
                                 | (CONF_EIC_FILTEN13 << EIC_CONFIG_FILTEN5_Pos) | EIC_CONFIG_SENSE5(CONF_EIC_SENSE13)
                                 | (CONF_EIC_FILTEN14 << EIC_CONFIG_FILTEN6_Pos) | EIC_CONFIG_SENSE6(CONF_EIC_SENSE14)
                                 | (CONF_EIC_FILTEN15 << EIC_CONFIG_FILTEN7_Pos) | EIC_CONFIG_SENSE7(CONF_EIC_SENSE15)
                                 | 0);

    hri_eic_set_CTRLA_ENABLE_bit(EIC);

    NVIC_SetStateIRQ(EIC_0_IRQn, true);
    NVIC_SetStateIRQ(EIC_1_IRQn, true);
    NVIC_SetStateIRQ(EIC_2_IRQn, true);
    NVIC_SetStateIRQ(EIC_3_IRQn, true);
    NVIC_SetStateIRQ(EIC_4_IRQn, true);
    NVIC_SetStateIRQ(EIC_5_IRQn, true);
    NVIC_SetStateIRQ(EIC_6_IRQn, true);
    NVIC_SetStateIRQ(EIC_7_IRQn, true);
    NVIC_SetStateIRQ(EIC_8_IRQn, true);
    NVIC_SetStateIRQ(EIC_9_IRQn, true);
    NVIC_SetStateIRQ(EIC_10_IRQn, true);
    NVIC_SetStateIRQ(EIC_11_IRQn, true);
    NVIC_SetStateIRQ(EIC_12_IRQn, true);
    NVIC_SetStateIRQ(EIC_13_IRQn, true);
    NVIC_SetStateIRQ(EIC_14_IRQn, true);
    NVIC_SetStateIRQ(EIC_15_IRQn, true);

    return ERR_NONE;
}

/**
 * \brief De-initialize external interrupt module
 */
int32_t _ext_irq_deinit(void)
{
    NVIC_SetStateIRQ(EIC_0_IRQn, false);
    NVIC_SetStateIRQ(EIC_1_IRQn, false);
    NVIC_SetStateIRQ(EIC_2_IRQn, false);
    NVIC_SetStateIRQ(EIC_3_IRQn, false);
    NVIC_SetStateIRQ(EIC_4_IRQn, false);
    NVIC_SetStateIRQ(EIC_5_IRQn, false);
    NVIC_SetStateIRQ(EIC_6_IRQn, false);
    NVIC_SetStateIRQ(EIC_7_IRQn, false);
    NVIC_SetStateIRQ(EIC_8_IRQn, false);
    NVIC_SetStateIRQ(EIC_9_IRQn, false);
    NVIC_SetStateIRQ(EIC_10_IRQn, false);
    NVIC_SetStateIRQ(EIC_11_IRQn, false);
    NVIC_SetStateIRQ(EIC_12_IRQn, false);
    NVIC_SetStateIRQ(EIC_13_IRQn, false);
    NVIC_SetStateIRQ(EIC_14_IRQn, false);
    NVIC_SetStateIRQ(EIC_15_IRQn, false);

    for (uint32_t i = 0u; i < EXT_IRQ_AMOUNT; i++)
    {
        extis[i].callback = NULL;
        extis[i].data = NULL;
    }

    hri_eic_clear_CTRLA_ENABLE_bit(EIC);
    hri_eic_set_CTRLA_SWRST_bit(EIC);

    return ERR_NONE;
}

/**
 * \brief Enable / disable external irq
 */
int32_t _ext_irq_enable(const uint32_t pin, const bool enable, ext_irq_cb_t callback, void* user_data)
{
    uint8_t extint = 0u;

    while (extint < EXT_IRQ_AMOUNT && _exti_ch_pins[extint] != pin)
    {
        extint++;
    }

    if (extint == EXT_IRQ_AMOUNT)
    {
        return -1;
    }

    if (enable) {
        extis[extint].callback = callback;
        extis[extint].data = user_data;
        hri_eic_set_INTEN_reg(EIC, 1ul << extint);
    } else {
        hri_eic_clear_INTEN_reg(EIC, 1ul << extint);
        hri_eic_clear_INTFLAG_reg(EIC, 1ul << extint);
        NVIC_ClearPendingIRQ(EIC_0_IRQn + extint);
    }

    return ERR_NONE;
}

/**
 * \brief Inter EIC interrupt handler
 */
static void _ext_irq_handler(uint32_t pos)
{
    hri_eic_clear_INTFLAG_reg(EIC, 1u << pos);
    if (extis[pos].callback) {
        extis[pos].callback(extis[pos].data);
    }
}

void EIC_0_Handler(void)
{
    _ext_irq_handler(0u);
}
void EIC_1_Handler(void)
{
    _ext_irq_handler(1u);
}
void EIC_2_Handler(void)
{
    _ext_irq_handler(2u);
}
void EIC_3_Handler(void)
{
    _ext_irq_handler(3u);
}
void EIC_4_Handler(void)
{
    _ext_irq_handler(4u);
}
void EIC_5_Handler(void)
{
    _ext_irq_handler(5u);
}
void EIC_6_Handler(void)
{
    _ext_irq_handler(6u);
}
void EIC_7_Handler(void)
{
    _ext_irq_handler(7u);
}
void EIC_8_Handler(void)
{
    _ext_irq_handler(8u);
}
void EIC_9_Handler(void)
{
    _ext_irq_handler(9u);
}
void EIC_10_Handler(void)
{
    _ext_irq_handler(10u);
}
void EIC_11_Handler(void)
{
    _ext_irq_handler(11u);
}
void EIC_12_Handler(void)
{
    _ext_irq_handler(12u);
}
void EIC_13_Handler(void)
{
    _ext_irq_handler(13u);
}
void EIC_14_Handler(void)
{
    _ext_irq_handler(14u);
}
void EIC_15_Handler(void)
{
    _ext_irq_handler(15u);
}


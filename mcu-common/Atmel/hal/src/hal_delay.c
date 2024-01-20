/**
 * \file
 *
 * \brief HAL delay related functionality implementation.
 *
 * Copyright (c) 2014-2018 Microchip Technology Inc. and its subsidiaries.
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

#include <hpl_irq.h>
#include <hpl_reset.h>
#include <hpl_sleep.h>
#include "hal_delay.h"
#include <hpl_delay.h>
#include <hpl_time_measure.h>
#include <utils_assert.h>

/**
 * \brief Driver version
 */
#define DRIVER_VERSION 0x00000001u

/**
 * \brief The pointer to a hardware instance used by the driver.
 */
static void *hardware;

/**
 * \brief Initialize Delay driver
 */
void delay_init(void *const hw)
{
    ASSERT(hw);
    hardware = hw;
    _delay_init(hardware);
}

/**
 * \brief Perform delay in us
 */
void delay_us(const uint16_t us)
{
	_delay_cycles(hardware, _get_cycles_for_us(us));
}

/**
 * \brief Perform delay in ms
 */
void delay_ms(const uint16_t ms)
{
	_delay_cycles(hardware, _get_cycles_for_ms(ms));
}

/**
 * \brief Retrieve the current driver version
 */
uint32_t delay_get_version(void)
{
	return DRIVER_VERSION;
}

uint32_t get_system_tick(void)
{
	return _system_time_get(hardware);
}

uint32_t get_cycles_for_1ms(void)
{
	return _get_cycles_for_ms(1);
}

uint32_t get_cycles_for_1us(void)
{
	return _get_cycles_for_us(1);
}

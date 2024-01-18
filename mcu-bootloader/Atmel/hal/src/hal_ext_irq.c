/**
 * \file
 *
 * \brief External interrupt functionality imkplementation.
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

#include "hal_ext_irq.h"

/**
 * \brief Driver version
 */
#define DRIVER_VERSION 0x00000001u


/**
 * \brief Initialize external irq component if any
 */
int32_t ext_irq_init(void)
{
	return _ext_irq_init();
}

/**
 * \brief Deinitialize external irq if any
 */
int32_t ext_irq_deinit(void)
{
	return _ext_irq_deinit();
}

/**
 * \brief Enable external irq
 */
int32_t ext_irq_enable(const uint32_t pin, ext_irq_cb_t callback, void* user_data)
{
	return _ext_irq_enable(pin, true, callback, user_data);
}

/**
 * \brief Disable external irq
 */
int32_t ext_irq_disable(const uint32_t pin)
{
	return _ext_irq_enable(pin, false, NULL, NULL);
}

void ext_irq_clear_pending(const uint32_t pin)
{
  _ext_irq_clear_pending(pin);
}

/**
 * \brief Retrieve the current driver version
 */
uint32_t ext_irq_get_version(void)
{
	return DRIVER_VERSION;
}

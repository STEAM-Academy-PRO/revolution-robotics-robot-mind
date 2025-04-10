/**
 * \file
 *
 * \brief I2C Slave Hardware Proxy Layer(HPL) declaration.
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
#ifndef _HPL_I2C_S_SYNC_H_INCLUDED
#define _HPL_I2C_S_SYNC_H_INCLUDED

#include <compiler.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
	void *const hw;
	hri_sercomi2cs_ctrla_reg_t ctrl_a;
	hri_sercomi2cs_ctrlb_reg_t ctrl_b;
	hri_sercomi2cs_addr_reg_t  address;
} i2cs_config_t;

/**
 * \brief I2C Slave status type
 */
typedef uint32_t i2c_s_status_t;

/**
 * \brief i2c slave device structure
 */
struct _i2c_s_sync_device {
	void *hw;
};

#include <compiler.h>

/**
 * \name HPL functions
 */

/**
 * \brief Initialize synchronous I2C slave
 *
 * This function does low level I2C configuration.
 *
 * \param[in] device The pointer to i2c slave device structure
 *
 * \return Return 0 for success and negative value for error
 */
int32_t _i2c_s_sync_init(struct _i2c_s_sync_device *const device, i2cs_config_t* config);

/**
 * \brief Deinitialize synchronous I2C slave
 *
 * \param[in] device The pointer to i2c slave device structure
 *
 * \return Return 0 for success and negative value for error
 */
int32_t _i2c_s_sync_deinit(struct _i2c_s_sync_device *const device);

/**
 * \brief Enable I2C module
 *
 * This function does low level I2C enable.
 *
 * \param[in] device The pointer to i2c slave device structure
 *
 * \return Return 0 for success and negative value for error
 */
int32_t _i2c_s_sync_enable(struct _i2c_s_sync_device *const device);

/**
 * \brief Disable I2C module
 *
 * This function does low level I2C disable.
 *
 * \param[in] device The pointer to i2c slave device structure
 *
 * \return Return 0 for success and negative value for error
 */
int32_t _i2c_s_sync_disable(struct _i2c_s_sync_device *const device);

/**
 * \brief Check if 10-bit addressing mode is on
 *
 * \param[in] device The pointer to i2c slave device structure
 *
 * \return Cheking status
 * \retval 1 10-bit addressing mode is on
 * \retval 0 10-bit addressing mode is off
 */
int32_t _i2c_s_sync_is_10bit_addressing_on(const struct _i2c_s_sync_device *const device);

/**
 * \brief Set I2C slave address
 *
 * \param[in] device The pointer to i2c slave device structure
 * \param[in] address Address to set
 *
 * \return Return 0 for success and negative value for error
 */
int32_t _i2c_s_sync_set_address(struct _i2c_s_sync_device *const device, const uint16_t address);

/**
 * \brief Write a byte to the given I2C instance
 *
 * \param[in] device The pointer to i2c slave device structure
 * \param[in] data Data to write
 */
void _i2c_s_sync_write_byte(struct _i2c_s_sync_device *const device, const uint8_t data);

/**
 * \brief Retrieve I2C slave status
 *
 * \param[in] device The pointer to i2c slave device structure
 *
 *\return I2C slave status
 */
i2c_s_status_t _i2c_s_sync_get_status(const struct _i2c_s_sync_device *const device);

/**
 * \brief Clear the Data Ready interrupt flag
 *
 * \param[in] device The pointer to i2c slave device structure
 *
 * \return Return 0 for success and negative value for error
 */
int32_t _i2c_s_sync_clear_data_ready_flag(const struct _i2c_s_sync_device *const device);

/**
 * \brief Read a byte from the given I2C instance
 *
 * \param[in] device The pointer to i2c slave device structure
 *
 * \return Data received via I2C interface.
 */
uint8_t _i2c_s_sync_read_byte(const struct _i2c_s_sync_device *const device);

/**
 * \brief Check if I2C is ready to send next byte
 *
 * \param[in] device The pointer to i2c slave device structure
 *
 * \return Status of the ready check.
 * \retval true if the I2C is ready to send next byte
 * \retval false if the I2C is not ready to send next byte
 */
bool _i2c_s_sync_is_byte_sent(const struct _i2c_s_sync_device *const device);

/**
 * \brief Check if there is data received by I2C
 *
 * \param[in] device The pointer to i2c slave device structure
 *
 * \return Status of the data received check.
 * \retval true if the I2C has received a byte
 * \retval false if the I2C has not received a byte
 */
bool _i2c_s_sync_is_byte_received(const struct _i2c_s_sync_device *const device);

#ifdef __cplusplus
}
#endif

#endif /* _HPL_I2C_S_SYNC_H_INCLUDED */


/**
 * \file
 *
 * \brief SAM Serial Communication Interface
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

#include <hpl_sercom_config.h>
#include <hpl_dma.h>
#include <hpl_i2c_s_async.h>
#include <hpl_spi_m_async.h>
#include <hpl_spi_m_sync.h>
#include <hpl_spi_s_async.h>
#include <hpl_spi_s_sync.h>
#include <hpl_spi_m_dma.h>
#include <utils.h>
#include <utils_assert.h>

static struct _i2c_s_async_device *_sercom2_dev = NULL;

static uint8_t _sercom_get_irq_num(const void *const hw);
static void    _sercom_init_irq_param(const void *const hw, void *dev);
static int8_t _sercom_get_hardware_index(const void *const hw);

/**
 * \brief Retrieve ordinal number of the given sercom hardware instance
 */
static int8_t _sercom_get_hardware_index(const void *const hw)
{
	Sercom *const sercom_modules[] = SERCOM_INSTS;
	/* Find index for SERCOM instance. */
	for (uint32_t i = 0; i < SERCOM_INST_NUM; i++) {
		if ((uint32_t)hw == (uint32_t)sercom_modules[i]) {
			return i;
		}
	}
    ASSERT(0);
	return -1;
}

/**
 * \brief Init irq param with the given sercom hardware instance
 */
static void _sercom_init_irq_param(const void *const hw, void *dev)
{
	if (hw == SERCOM2)
    {
		_sercom2_dev = (struct _i2c_s_async_device *)dev;
	}
    else
    {
        ASSERT(0);
    }
}

/* Sercom I2C implementation */
/**
 * \brief Retrieve IRQ number for the given hardware instance
 */
static uint8_t _sercom_get_irq_num(const void *const hw)
{
	return SERCOM0_0_IRQn + (_sercom_get_hardware_index(hw) << 2);
}

/* SERCOM I2C slave */

#ifndef CONF_SERCOM_2_I2CS_ENABLE
#define CONF_SERCOM_2_I2CS_ENABLE 0
#endif
#ifndef CONF_SERCOM_4_I2CS_ENABLE
#define CONF_SERCOM_4_I2CS_ENABLE 0
#endif
#ifndef CONF_SERCOM_5_I2CS_ENABLE
#define CONF_SERCOM_5_I2CS_ENABLE 0
#endif
#ifndef CONF_SERCOM_7_I2CS_ENABLE
#define CONF_SERCOM_7_I2CS_ENABLE 0
#endif

/** Amount of SERCOM that is used as I2C Slave. */
#define SERCOM_I2CS_AMOUNT                                                                                             \
	(CONF_SERCOM_2_I2CS_ENABLE + CONF_SERCOM_4_I2CS_ENABLE + CONF_SERCOM_5_I2CS_ENABLE + CONF_SERCOM_7_I2CS_ENABLE)

/**
 * \brief Macro to check 10-bit addressing
 */
#define I2CS_7BIT_ADDRESSING_MASK 0x7F

static int32_t     _i2c_s_init(i2cs_config_t* config);
static inline void _i2c_s_deinit(void *const hw);
static int32_t     _i2c_s_set_address(void *const hw, const uint16_t address);

/**
 * \brief Initialize synchronous I2C slave
 */
int32_t _i2c_s_sync_init(struct _i2c_s_sync_device *const device, i2cs_config_t* config)
{
	ASSERT(device);

	int32_t status = _i2c_s_init(config);
	if (status) {
		return status;
	}
	device->hw = config->hw;

	return ERR_NONE;
}

/**
 * \brief Initialize asynchronous I2C slave
 */
int32_t _i2c_s_async_init(struct _i2c_s_async_device *const device, i2cs_config_t* config)
{
	ASSERT(device);

	int32_t init_status = _i2c_s_init(config);
	if (init_status) {
		return init_status;
	}

	device->hw = config->hw;
	_sercom_init_irq_param(config->hw, (void *)device);
	uint8_t irq = _sercom_get_irq_num(config->hw);
	for (uint32_t i = 0; i < 4; i++) {
		NVIC_DisableIRQ((IRQn_Type)irq);
		NVIC_ClearPendingIRQ((IRQn_Type)irq);
		NVIC_EnableIRQ((IRQn_Type)irq);
		irq++;
	}

	return ERR_NONE;
}

/**
 * \brief Deinitialize synchronous I2C
 */
int32_t _i2c_s_sync_deinit(struct _i2c_s_sync_device *const device)
{
	_i2c_s_deinit(device->hw);

	return ERR_NONE;
}

/**
 * \brief Deinitialize asynchronous I2C
 */
int32_t _i2c_s_async_deinit(struct _i2c_s_async_device *const device)
{
	NVIC_DisableIRQ((IRQn_Type)_sercom_get_irq_num(device->hw));
	_i2c_s_deinit(device->hw);

	return ERR_NONE;
}

/**
 * \brief Enable I2C module
 */
int32_t _i2c_s_sync_enable(struct _i2c_s_sync_device *const device)
{
	hri_sercomi2cs_set_CTRLA_ENABLE_bit(device->hw);

	return ERR_NONE;
}

/**
 * \brief Enable I2C module
 */
int32_t _i2c_s_async_enable(struct _i2c_s_async_device *const device)
{
    ASSERT(device->cb.stop_cb);
    ASSERT(device->cb.addrm_cb);
    ASSERT(device->cb.error_cb);

	// Enable all interrupt requests
	hri_sercomi2cs_set_INTEN_ERROR_bit(device->hw);
	hri_sercomi2cs_set_INTEN_AMATCH_bit(device->hw);
	hri_sercomi2cs_set_INTEN_PREC_bit(device->hw);
	hri_sercomi2cs_set_INTEN_DRDY_bit(device->hw);

	// Enable the peripheral
	hri_sercomi2cs_set_CTRLA_ENABLE_bit(device->hw);

	return ERR_NONE;
}

/**
 * \brief Disable I2C module
 */
int32_t _i2c_s_sync_disable(struct _i2c_s_sync_device *const device)
{
	hri_sercomi2cs_clear_CTRLA_ENABLE_bit(device->hw);

	return ERR_NONE;
}

/**
 * \brief Disable I2C module
 */
int32_t _i2c_s_async_disable(struct _i2c_s_async_device *const device)
{
	hri_sercomi2cs_clear_CTRLA_ENABLE_bit(device->hw);

	return ERR_NONE;
}

/**
 * \brief Check if 10-bit addressing mode is on
 */
int32_t _i2c_s_sync_is_10bit_addressing_on(const struct _i2c_s_sync_device *const device)
{
	return hri_sercomi2cs_get_ADDR_TENBITEN_bit(device->hw);
}

/**
 * \brief Check if 10-bit addressing mode is on
 */
int32_t _i2c_s_async_is_10bit_addressing_on(const struct _i2c_s_async_device *const device)
{
	return hri_sercomi2cs_get_ADDR_TENBITEN_bit(device->hw);
}

/**
 * \brief Set I2C slave address
 */
int32_t _i2c_s_sync_set_address(struct _i2c_s_sync_device *const device, const uint16_t address)
{
    ASSERT(device);
    ASSERT(device->hw);
	return _i2c_s_set_address(device->hw, address);
}

/**
 * \brief Set I2C slave address
 */
int32_t _i2c_s_async_set_address(struct _i2c_s_async_device *const device, const uint16_t address)
{
    ASSERT(device);
    ASSERT(device->hw);
	return _i2c_s_set_address(device->hw, address);
}

/**
 * \brief Write a byte to the given I2C instance
 */
void _i2c_s_sync_write_byte(struct _i2c_s_sync_device *const device, const uint8_t data)
{
	hri_sercomi2cs_write_DATA_reg(device->hw, data);
}

/**
 * \brief Write a byte to the given I2C instance
 */
void _i2c_s_async_write_byte(struct _i2c_s_async_device *const device, const uint8_t data)
{
#if I2CS_DATA_DELAY > 0
	// Delay writing the DATA register by a bit. I don't know why we need this, but I think
	// there is a hardware race between short clock LOW states and writing the DATA register.
	for (uint32_t i = 0; i < I2CS_DATA_DELAY; i++) {
		__NOP();
	}
#endif

	hri_sercomi2cs_write_DATA_reg(device->hw, data);
}

/**
 * \brief Read a byte from the given I2C instance
 */
uint8_t _i2c_s_sync_read_byte(const struct _i2c_s_sync_device *const device)
{
	return hri_sercomi2cs_read_DATA_reg(device->hw);
}

/**
 * \brief Check if I2C is ready to send next byt
 */
bool _i2c_s_sync_is_byte_sent(const struct _i2c_s_sync_device *const device)
{
	return hri_sercomi2cs_get_interrupt_DRDY_bit(device->hw);
}

/**
 * \brief Check if there is data received by I2C
 */
bool _i2c_s_sync_is_byte_received(const struct _i2c_s_sync_device *const device)
{
	return hri_sercomi2cs_get_interrupt_DRDY_bit(device->hw);
}

/**
 * \brief Retrieve I2C slave status
 */
i2c_s_status_t _i2c_s_sync_get_status(const struct _i2c_s_sync_device *const device)
{
	return hri_sercomi2cs_read_STATUS_reg(device->hw);
}

/**
 * \brief Clear the Data Ready interrupt flag
 */
int32_t _i2c_s_sync_clear_data_ready_flag(const struct _i2c_s_sync_device *const device)
{
	hri_sercomi2cs_clear_INTFLAG_DRDY_bit(device->hw);

	return ERR_NONE;
}

/**
 * \brief Retrieve I2C slave status
 */
i2c_s_status_t _i2c_s_async_get_status(const struct _i2c_s_async_device *const device)
{
	return hri_sercomi2cs_read_STATUS_reg(device->hw);
}

/**
 * \brief Abort data transmission
 */
int32_t _i2c_s_async_abort_transmission(const struct _i2c_s_async_device *const device)
{
	hri_sercomi2cs_clear_INTEN_DRDY_bit(device->hw);

	return ERR_NONE;
}

/**
 * \brief Enable/disable I2C slave interrupt
 */
int32_t _i2c_s_async_set_irq_state(struct _i2c_s_async_device *const device, const enum _i2c_s_async_callback_type type,
                                   const bool state)
{
    ASSERT(device);
    ASSERT(device->hw);

    switch (type)
    {
        case I2C_S_DEVICE_TX:
        case I2C_S_DEVICE_RX_COMPLETE:
            hri_sercomi2cs_write_INTEN_DRDY_bit(device->hw, state);
            break;

        case I2C_S_DEVICE_ERROR:
            hri_sercomi2cs_write_INTEN_ERROR_bit(device->hw, state);
            break;

        default:
            ASSERT(0);
            return ERR_INVALID_ARG;
    }

    return ERR_NONE;
}

/**
 * \internal Sercom i2c slave interrupt handler
 *
 * \param[in] p The pointer to i2c slave device
 */
static void _sercom_i2c_s_irq_handler_0(struct _i2c_s_async_device *device)
{
    SercomI2cs* hw = device->hw;
    device->cb.stop_cb(hri_sercomi2cs_get_STATUS_DIR_bit(hw));
    hri_sercomi2cs_clear_INTFLAG_PREC_bit(hw);
}

static void _sercom_i2c_s_irq_handler_1(struct _i2c_s_async_device *device)
{
    SercomI2cs* hw = device->hw;
    device->cb.addrm_cb(hri_sercomi2cs_get_STATUS_DIR_bit(hw));
    hri_sercomi2cs_clear_INTFLAG_AMATCH_bit(hw);
}

static void _sercom_i2c_s_irq_handler_2(struct _i2c_s_async_device *device)
{
    SercomI2cs* hw = device->hw;
    if (hri_sercomi2cs_get_STATUS_DIR_bit(hw)) {
        sercom2_tx_cb();
    } else {
        sercom2_rx_done_cb((uint8_t) hri_sercomi2cs_read_DATA_reg(hw));
    }
}

__attribute__((weak))
void sercom2_tx_cb(void) {

}

__attribute__((weak))
void sercom2_rx_done_cb(uint8_t data)
{
    (void) data;
}

static void _sercom_i2c_s_irq_handler_3(struct _i2c_s_async_device *device)
{
    SercomI2cs* hw = device->hw;
    hri_sercomi2cs_clear_INTFLAG_ERROR_bit(hw);
    device->cb.error_cb();
}

/**
 * \internal Initalize i2c slave hardware
 *
 * \param[in] p The pointer to hardware instance
 *
 *\ return status of initialization
 */
static int32_t _i2c_s_init(i2cs_config_t* config)
{
	void *const hw = config->hw;

	if (!hri_sercomi2cs_is_syncing(hw, SERCOM_I2CS_CTRLA_SWRST)) {
		uint32_t mode = config->ctrl_a & SERCOM_I2CS_CTRLA_MODE_Msk;
		if (hri_sercomi2cs_get_CTRLA_reg(hw, SERCOM_I2CS_CTRLA_ENABLE)) {
			hri_sercomi2cs_clear_CTRLA_ENABLE_bit(hw);
			hri_sercomi2cs_wait_for_sync(hw, SERCOM_I2CS_SYNCBUSY_ENABLE);
		}
		hri_sercomi2cs_write_CTRLA_reg(hw, SERCOM_I2CS_CTRLA_SWRST | mode);
	}
	hri_sercomi2cs_wait_for_sync(hw, SERCOM_I2CS_SYNCBUSY_SWRST);

	hri_sercomi2cs_write_CTRLA_reg(hw, config->ctrl_a);
	hri_sercomi2cs_write_CTRLB_reg(hw, config->ctrl_b);
	hri_sercomi2cs_write_ADDR_reg(hw, config->address);

	return ERR_NONE;
}

/**
 * \internal De-initialize i2c slave
 *
 * \param[in] hw The pointer to hardware instance
 */
static inline void _i2c_s_deinit(void *const hw)
{
	hri_sercomi2cs_clear_CTRLA_ENABLE_bit(hw);
	hri_sercomi2cs_set_CTRLA_SWRST_bit(hw);
}

/**
 * \internal De-initialize i2c slave
 *
 * \param[in] hw The pointer to hardware instance
 * \param[in] address Address to set
 */
static int32_t _i2c_s_set_address(void *const hw, const uint16_t address)
{
	bool was_enabled = hri_sercomi2cs_get_CTRLA_ENABLE_bit(hw);

	CRITICAL_SECTION_ENTER()
	hri_sercomi2cs_clear_CTRLA_ENABLE_bit(hw);
	hri_sercomi2cs_write_ADDR_ADDR_bf(hw, address);
	CRITICAL_SECTION_LEAVE()

	if (was_enabled) {
		hri_sercomi2cs_set_CTRLA_ENABLE_bit(hw);
	}

	return ERR_NONE;
}

	/* Sercom SPI implementation */

#ifndef SERCOM_USART_CTRLA_MODE_SPI_SLAVE
#define SERCOM_USART_CTRLA_MODE_SPI_SLAVE (2 << 2)
#endif

#define SPI_DEV_IRQ_MODE 0x8000

#define _SPI_CS_PORT_EXTRACT(cs) (((cs) >> 0) & 0xFF)
#define _SPI_CS_PIN_EXTRACT(cs) (((cs) >> 8) & 0xFF)

COMPILER_PACK_SET(1)
/** Initialization configuration of registers. */
struct sercomspi_regs_cfg {
	uint32_t ctrla;
	uint32_t ctrlb;
	uint32_t addr;
	uint8_t  baud;
	uint8_t  dbgctrl;
	uint16_t dummy_byte;
	uint8_t  n;
};
COMPILER_PACK_RESET()

/** Build configuration from header macros. */
#define SERCOMSPI_REGS(n)                                                                                              \
	{                                                                                                                  \
		(((CONF_SERCOM_##n##_SPI_DORD) << SERCOM_SPI_CTRLA_DORD_Pos)                                                   \
		 | (CONF_SERCOM_##n##_SPI_CPOL << SERCOM_SPI_CTRLA_CPOL_Pos)                                                   \
		 | (CONF_SERCOM_##n##_SPI_CPHA << SERCOM_SPI_CTRLA_CPHA_Pos)                                                   \
		 | (CONF_SERCOM_##n##_SPI_AMODE_EN ? SERCOM_SPI_CTRLA_FORM(2) : SERCOM_SPI_CTRLA_FORM(0))                      \
		 | SERCOM_SPI_CTRLA_DOPO(CONF_SERCOM_##n##_SPI_TXPO) | SERCOM_SPI_CTRLA_DIPO(CONF_SERCOM_##n##_SPI_RXPO)       \
		 | (CONF_SERCOM_##n##_SPI_IBON << SERCOM_SPI_CTRLA_IBON_Pos)                                                   \
		 | (CONF_SERCOM_##n##_SPI_RUNSTDBY << SERCOM_SPI_CTRLA_RUNSTDBY_Pos)                                           \
		 | SERCOM_SPI_CTRLA_MODE(CONF_SERCOM_##n##_SPI_MODE)), /* ctrla */                                             \
		    ((CONF_SERCOM_##n##_SPI_RXEN << SERCOM_SPI_CTRLB_RXEN_Pos)                                                 \
		     | (CONF_SERCOM_##n##_SPI_MSSEN << SERCOM_SPI_CTRLB_MSSEN_Pos)                                             \
		     | (CONF_SERCOM_##n##_SPI_SSDE << SERCOM_SPI_CTRLB_SSDE_Pos)                                               \
		     | (CONF_SERCOM_##n##_SPI_PLOADEN << SERCOM_SPI_CTRLB_PLOADEN_Pos)                                         \
		     | SERCOM_SPI_CTRLB_AMODE(CONF_SERCOM_##n##_SPI_AMODE)                                                     \
		     | SERCOM_SPI_CTRLB_CHSIZE(CONF_SERCOM_##n##_SPI_CHSIZE)), /* ctrlb */                                     \
		    (SERCOM_SPI_ADDR_ADDR(CONF_SERCOM_##n##_SPI_ADDR)                                                          \
		     | SERCOM_SPI_ADDR_ADDRMASK(CONF_SERCOM_##n##_SPI_ADDRMASK)),      /* addr */                              \
		    ((uint8_t)CONF_SERCOM_##n##_SPI_BAUD_RATE),                        /* baud */                              \
		    (CONF_SERCOM_##n##_SPI_DBGSTOP << SERCOM_SPI_DBGCTRL_DBGSTOP_Pos), /* dbgctrl */                           \
		    CONF_SERCOM_##n##_SPI_DUMMYBYTE,                                   /* Dummy byte for SPI master mode */    \
		    n                                                                  /* sercom number */                     \
	}

#ifndef CONF_SERCOM_2_SPI_ENABLE
#define CONF_SERCOM_2_SPI_ENABLE 0
#endif
#ifndef CONF_SERCOM_4_SPI_ENABLE
#define CONF_SERCOM_4_SPI_ENABLE 0
#endif
#ifndef CONF_SERCOM_5_SPI_ENABLE
#define CONF_SERCOM_5_SPI_ENABLE 0
#endif
#ifndef CONF_SERCOM_7_SPI_ENABLE
#define CONF_SERCOM_7_SPI_ENABLE 0
#endif

/** Amount of SERCOM that is used as SPI */
#define SERCOM_SPI_AMOUNT                                                                                              \
	(CONF_SERCOM_2_SPI_ENABLE + CONF_SERCOM_4_SPI_ENABLE + CONF_SERCOM_5_SPI_ENABLE + CONF_SERCOM_7_SPI_ENABLE)

#if SERCOM_SPI_AMOUNT < 1
/** Dummy array for compiling. */
static const struct sercomspi_regs_cfg sercomspi_regs[1] = {{0}};
#else
/** The SERCOM SPI configurations of SERCOM that is used as SPI. */
static const struct sercomspi_regs_cfg sercomspi_regs[] = {
#if CONF_SERCOM_2_SPI_ENABLE
    SERCOMSPI_REGS(2),
#endif
#if CONF_SERCOM_4_SPI_ENABLE
    SERCOMSPI_REGS(4),
#endif
#if CONF_SERCOM_5_SPI_ENABLE
    SERCOMSPI_REGS(5),
#endif
#if CONF_SERCOM_7_SPI_ENABLE
    SERCOMSPI_REGS(7),
#endif
};
#endif

/** \internal De-initialize SERCOM SPI
 *
 *  \param[in] hw Pointer to the hardware register base.
 *
 * \return De-initialization status
 */
static int32_t _spi_deinit(void *const hw)
{
	hri_sercomspi_clear_CTRLA_ENABLE_bit(hw);
	hri_sercomspi_set_CTRLA_SWRST_bit(hw);

	return ERR_NONE;
}

/** \internal Enable SERCOM SPI
 *
 *  \param[in] hw Pointer to the hardware register base.
 *
 * \return Enabling status
 */
static int32_t _spi_sync_enable(void *const hw)
{
	if (hri_sercomspi_is_syncing(hw, SERCOM_SPI_SYNCBUSY_SWRST)) {
		return ERR_BUSY;
	}

	hri_sercomspi_set_CTRLA_ENABLE_bit(hw);

	return ERR_NONE;
}

/** \internal Enable SERCOM SPI
 *
 *  \param[in] hw Pointer to the hardware register base.
 *
 * \return Enabling status
 */
static int32_t _spi_async_enable(void *const hw)
{
	_spi_sync_enable(hw);
	uint8_t irq = _sercom_get_irq_num(hw);
	for (uint32_t i = 0; i < 4; i++) {
		NVIC_EnableIRQ((IRQn_Type)irq++);
	}

	return ERR_NONE;
}

/** \internal Disable SERCOM SPI
 *
 *  \param[in] hw Pointer to the hardware register base.
 *
 * \return Disabling status
 */
static int32_t _spi_sync_disable(void *const hw)
{
	if (hri_sercomspi_is_syncing(hw, SERCOM_SPI_SYNCBUSY_SWRST)) {
		return ERR_BUSY;
	}
	hri_sercomspi_clear_CTRLA_ENABLE_bit(hw);

	return ERR_NONE;
}

/** \internal Disable SERCOM SPI
 *
 *  \param[in] hw Pointer to the hardware register base.
 *
 * \return Disabling status
 */
static int32_t _spi_async_disable(void *const hw)
{
	_spi_sync_disable(hw);
	hri_sercomspi_clear_INTEN_reg(
	    hw, SERCOM_SPI_INTFLAG_ERROR | SERCOM_SPI_INTFLAG_RXC | SERCOM_SPI_INTFLAG_TXC | SERCOM_SPI_INTFLAG_DRE);
	uint8_t irq = _sercom_get_irq_num(hw);
	for (uint32_t i = 0; i < 4; i++) {
		NVIC_DisableIRQ((IRQn_Type)irq++);
	}

	return ERR_NONE;
}

/** \internal Set SERCOM SPI mode
 *
 * \param[in] hw Pointer to the hardware register base.
 * \param[in] mode The mode to set
 *
 * \return Setting mode status
 */
static int32_t _spi_set_mode(void *const hw, const enum spi_transfer_mode mode)
{
	uint32_t ctrla;

	if (hri_sercomspi_is_syncing(hw, SERCOM_SPI_SYNCBUSY_SWRST | SERCOM_SPI_SYNCBUSY_ENABLE)) {
		return ERR_BUSY;
	}

	ctrla = hri_sercomspi_read_CTRLA_reg(hw);
	ctrla &= ~(SERCOM_SPI_CTRLA_CPOL | SERCOM_SPI_CTRLA_CPHA);
	ctrla |= (mode & 0x3u) << SERCOM_SPI_CTRLA_CPHA_Pos;
	hri_sercomspi_write_CTRLA_reg(hw, ctrla);

	return ERR_NONE;
}

/** \internal Set SERCOM SPI baudrate
 *
 * \param[in] hw Pointer to the hardware register base.
 * \param[in] baud_val The baudrate to set
 *
 * \return Setting baudrate status
 */
static int32_t _spi_set_baudrate(void *const hw, const uint32_t baud_val)
{
	if (hri_sercomspi_is_syncing(hw, SERCOM_SPI_SYNCBUSY_SWRST)) {
		return ERR_BUSY;
	}

	hri_sercomspi_write_BAUD_reg(hw, baud_val);

	return ERR_NONE;
}

/** \internal Set SERCOM SPI data order
 *
 * \param[in] hw Pointer to the hardware register base.
 * \param[in] baud_val The baudrate to set
 *
 * \return Setting data order status
 */
static int32_t _spi_set_data_order(void *const hw, const enum spi_data_order dord)
{
    ASSERT(hw);
    if (hri_sercomspi_is_syncing(hw, SERCOM_SPI_SYNCBUSY_SWRST)) {
        return ERR_BUSY;
    }

    switch (dord) {
        case SPI_DATA_ORDER_LSB_1ST:
            hri_sercomspi_set_CTRLA_DORD_bit(hw);
            break;

        case SPI_DATA_ORDER_MSB_1ST:
            hri_sercomspi_clear_CTRLA_DORD_bit(hw);
            break;

        default:
            ASSERT(0);
            return ERR_INVALID_ARG;
    }

    return ERR_NONE;
}

/** \brief Load SERCOM registers to init for SPI master mode
 *  The settings will be applied with default master mode, unsupported things
 *  are ignored.
 *  \param[in, out] hw Pointer to the hardware register base.
 *  \param[in] regs Pointer to register configuration values.
 */
static inline void _spi_load_regs_master(void *const hw, const struct sercomspi_regs_cfg *regs)
{
    ASSERT(hw);
    ASSERT(regs);

	hri_sercomspi_write_CTRLA_reg(
	    hw, regs->ctrla & ~(SERCOM_SPI_CTRLA_IBON | SERCOM_SPI_CTRLA_ENABLE | SERCOM_SPI_CTRLA_SWRST));
	hri_sercomspi_write_CTRLB_reg(
	    hw,
	    (regs->ctrlb
	     & ~(SERCOM_SPI_CTRLB_MSSEN | SERCOM_SPI_CTRLB_AMODE_Msk | SERCOM_SPI_CTRLB_SSDE | SERCOM_SPI_CTRLB_PLOADEN))
	        | (SERCOM_SPI_CTRLB_RXEN));
	hri_sercomspi_write_BAUD_reg(hw, regs->baud);
	hri_sercomspi_write_DBGCTRL_reg(hw, regs->dbgctrl);
}

/** \brief Load SERCOM registers to init for SPI slave mode
 *  The settings will be applied with default slave mode, unsupported things
 *  are ignored.
 *  \param[in, out] hw Pointer to the hardware register base.
 *  \param[in] regs Pointer to register configuration values.
 */
static inline void _spi_load_regs_slave(void *const hw, const struct sercomspi_regs_cfg *regs)
{
    ASSERT(hw);
    ASSERT(regs);

	hri_sercomspi_write_CTRLA_reg(
	    hw, regs->ctrla & ~(SERCOM_SPI_CTRLA_IBON | SERCOM_SPI_CTRLA_ENABLE | SERCOM_SPI_CTRLA_SWRST));
	hri_sercomspi_write_CTRLB_reg(hw,
	                              (regs->ctrlb & ~(SERCOM_SPI_CTRLB_MSSEN))
	                                  | (SERCOM_SPI_CTRLB_RXEN | SERCOM_SPI_CTRLB_SSDE | SERCOM_SPI_CTRLB_PLOADEN));
	hri_sercomspi_write_ADDR_reg(hw, regs->addr);
	hri_sercomspi_write_DBGCTRL_reg(hw, regs->dbgctrl);
	while (hri_sercomspi_is_syncing(hw, 0xFFFFFFFF))
		;
}

/** \brief Return the pointer to register settings of specific SERCOM
 *  \param[in] hw_addr The hardware register base address.
 *  \return Pointer to register settings of specific SERCOM.
 */
static inline const struct sercomspi_regs_cfg *_spi_get_regs(const uint32_t hw_addr)
{
	int8_t n = _sercom_get_hardware_index((const void *)hw_addr);

	for (uint8_t i = 0u; i < ARRAY_SIZE(sercomspi_regs); i++) {
		if (sercomspi_regs[i].n == n) {
			return &sercomspi_regs[i];
		}
	}

	return NULL;
}

/**
 * \internal Sercom interrupt handler
 */
void SERCOM2_0_Handler(void)
{
	_sercom_i2c_s_irq_handler_0(_sercom2_dev);
}
/**
 * \internal Sercom interrupt handler
 */
void SERCOM2_1_Handler(void)
{
	_sercom_i2c_s_irq_handler_1(_sercom2_dev);
}
/**
 * \internal Sercom interrupt handler
 */
void SERCOM2_2_Handler(void)
{
	_sercom_i2c_s_irq_handler_2(_sercom2_dev);
}
/**
 * \internal Sercom interrupt handler
 */
void SERCOM2_3_Handler(void)
{
	_sercom_i2c_s_irq_handler_3(_sercom2_dev);
}

void SERCOM4_0_Handler( void )
{

}
void SERCOM4_1_Handler( void )
{

}
void SERCOM4_2_Handler( void )
{

}
void SERCOM4_3_Handler( void )
{

}

int32_t _spi_m_sync_init(struct _spi_m_sync_dev *dev, void *const hw)
{
    ASSERT(dev);
    ASSERT(hw);

    const struct sercomspi_regs_cfg *regs = _spi_get_regs((uint32_t)hw);

	if (regs == NULL) {
		return ERR_INVALID_ARG;
	}

	if (!hri_sercomspi_is_syncing(hw, SERCOM_SPI_SYNCBUSY_SWRST)) {
		uint32_t mode = regs->ctrla & SERCOM_SPI_CTRLA_MODE_Msk;
		if (hri_sercomspi_get_CTRLA_reg(hw, SERCOM_SPI_CTRLA_ENABLE)) {
			hri_sercomspi_clear_CTRLA_ENABLE_bit(hw);
			hri_sercomspi_wait_for_sync(hw, SERCOM_SPI_SYNCBUSY_ENABLE);
		}
		hri_sercomspi_write_CTRLA_reg(hw, SERCOM_SPI_CTRLA_SWRST | mode);
	}
	hri_sercomspi_wait_for_sync(hw, SERCOM_SPI_SYNCBUSY_SWRST);

	dev->prvt = hw;

	if ((regs->ctrla & SERCOM_SPI_CTRLA_MODE_Msk) == SERCOM_USART_CTRLA_MODE_SPI_SLAVE) {
		_spi_load_regs_slave(hw, regs);
	} else {
		_spi_load_regs_master(hw, regs);
	}

	/* Load character size from default hardware configuration */
	dev->char_size = ((regs->ctrlb & SERCOM_SPI_CTRLB_CHSIZE_Msk) == 0) ? 1 : 2;

	dev->dummy_byte = regs->dummy_byte;

	return ERR_NONE;
}

int32_t _spi_s_sync_init(struct _spi_s_sync_dev *dev, void *const hw)
{
	return _spi_m_sync_init(dev, hw);
}

int32_t _spi_m_async_init(struct _spi_async_dev *dev, void *const hw)
{
	struct _spi_async_dev *spid = dev;
	/* Do hardware initialize. */
	int32_t rc = _spi_m_sync_init((struct _spi_m_sync_dev *)dev, hw);

	if (rc < 0) {
		return rc;
	}

	_sercom_init_irq_param(hw, (void *)dev);
	/* Initialize callbacks: must use them */
	spid->callbacks.complete = NULL;
	spid->callbacks.rx       = NULL;
	spid->callbacks.tx       = NULL;
	uint8_t irq              = _sercom_get_irq_num(hw);
	for (uint32_t i = 0; i < 4; i++) {
		NVIC_DisableIRQ((IRQn_Type)irq);
		NVIC_ClearPendingIRQ((IRQn_Type)irq);
		irq++;
	}

	return ERR_NONE;
}

int32_t _spi_s_async_init(struct _spi_s_async_dev *dev, void *const hw)
{
	return _spi_m_async_init(dev, hw);
}

int32_t _spi_m_async_deinit(struct _spi_async_dev *dev)
{
	NVIC_DisableIRQ((IRQn_Type)_sercom_get_irq_num(dev->prvt));
	NVIC_ClearPendingIRQ((IRQn_Type)_sercom_get_irq_num(dev->prvt));

	return _spi_deinit(dev->prvt);
}

int32_t _spi_s_async_deinit(struct _spi_s_async_dev *dev)
{
	NVIC_DisableIRQ((IRQn_Type)_sercom_get_irq_num(dev->prvt));
	NVIC_ClearPendingIRQ((IRQn_Type)_sercom_get_irq_num(dev->prvt));

	return _spi_deinit(dev->prvt);
}

int32_t _spi_m_sync_deinit(struct _spi_m_sync_dev *dev)
{
	ASSERT(dev);
    ASSERT(dev->prvt);
	return _spi_deinit(dev->prvt);
}

int32_t _spi_s_sync_deinit(struct _spi_s_sync_dev *dev)
{
	ASSERT(dev);
    ASSERT(dev->prvt);
	return _spi_deinit(dev->prvt);
}

int32_t _spi_m_sync_enable(struct _spi_m_sync_dev *dev)
{
	ASSERT(dev);
    ASSERT(dev->prvt);

	return _spi_sync_enable(dev->prvt);
}

int32_t _spi_s_sync_enable(struct _spi_s_sync_dev *dev)
{
	ASSERT(dev);
    ASSERT(dev->prvt);

	return _spi_sync_enable(dev->prvt);
}

int32_t _spi_m_async_enable(struct _spi_async_dev *dev)
{
	ASSERT(dev);
    ASSERT(dev->prvt);

	return _spi_async_enable(dev->prvt);
}

int32_t _spi_s_async_enable(struct _spi_s_async_dev *dev)
{
	ASSERT(dev);
    ASSERT(dev->prvt);

	return _spi_async_enable(dev->prvt);
}

int32_t _spi_m_sync_disable(struct _spi_m_sync_dev *dev)
{
	ASSERT(dev);
    ASSERT(dev->prvt);

	return _spi_sync_disable(dev->prvt);
}

int32_t _spi_s_sync_disable(struct _spi_s_sync_dev *dev)
{
	ASSERT(dev);
    ASSERT(dev->prvt);

	return _spi_sync_disable(dev->prvt);
}

int32_t _spi_m_async_disable(struct _spi_async_dev *dev)
{
	ASSERT(dev);
    ASSERT(dev->prvt);

	return _spi_async_disable(dev->prvt);
}

int32_t _spi_s_async_disable(struct _spi_s_async_dev *dev)
{
	ASSERT(dev);
    ASSERT(dev->prvt);

	return _spi_async_disable(dev->prvt);
}

int32_t _spi_m_sync_set_mode(struct _spi_m_sync_dev *dev, const enum spi_transfer_mode mode)
{
	ASSERT(dev);
    ASSERT(dev->prvt);

	return _spi_set_mode(dev->prvt, mode);
}

int32_t _spi_m_async_set_mode(struct _spi_async_dev *dev, const enum spi_transfer_mode mode)
{
	ASSERT(dev);
    ASSERT(dev->prvt);

	return _spi_set_mode(dev->prvt, mode);
}

int32_t _spi_s_async_set_mode(struct _spi_s_async_dev *dev, const enum spi_transfer_mode mode)
{
	ASSERT(dev);
    ASSERT(dev->prvt);

	return _spi_set_mode(dev->prvt, mode);
}

int32_t _spi_s_sync_set_mode(struct _spi_s_sync_dev *dev, const enum spi_transfer_mode mode)
{
	ASSERT(dev);
    ASSERT(dev->prvt);

	return _spi_set_mode(dev->prvt, mode);
}

int32_t _spi_calc_baud_val(struct spi_dev *dev, const uint32_t clk, const uint32_t baud)
{
    ASSERT(dev);
    ASSERT(clk);
    ASSERT(baud);

	/* Check baudrate range of current assigned clock */
	if (!(baud <= (clk >> 1) && baud >= (clk >> 8))) {
		return ERR_INVALID_ARG;
	}

	int32_t rc = ((clk >> 1) / baud) - 1;
	return rc;
}

int32_t _spi_m_sync_set_baudrate(struct _spi_m_sync_dev *dev, const uint32_t baud_val)
{
	ASSERT(dev);
    ASSERT(dev->prvt);

	return _spi_set_baudrate(dev->prvt, baud_val);
}

int32_t _spi_m_async_set_baudrate(struct _spi_async_dev *dev, const uint32_t baud_val)
{
	ASSERT(dev);
    ASSERT(dev->prvt);

	return _spi_set_baudrate(dev->prvt, baud_val);
}

int32_t _spi_m_sync_set_data_order(struct _spi_m_sync_dev *dev, const enum spi_data_order dord)
{
    ASSERT(dev);
    ASSERT(dev->prvt);

	return _spi_set_data_order(dev->prvt, dord);
}

int32_t _spi_m_async_set_data_order(struct _spi_async_dev *dev, const enum spi_data_order dord)
{
    ASSERT(dev);
    ASSERT(dev->prvt);

	return _spi_set_data_order(dev->prvt, dord);
}

int32_t _spi_s_async_set_data_order(struct _spi_s_async_dev *dev, const enum spi_data_order dord)
{
    ASSERT(dev);
    ASSERT(dev->prvt);

	return _spi_set_data_order(dev->prvt, dord);
}

int32_t _spi_s_sync_set_data_order(struct _spi_s_sync_dev *dev, const enum spi_data_order dord)
{
    ASSERT(dev);
    ASSERT(dev->prvt);

	return _spi_set_data_order(dev->prvt, dord);
}

/** Wait until SPI bus idle. */
static inline void _spi_wait_bus_idle(void *const hw)
{
	while (!(hri_sercomspi_get_INTFLAG_reg(hw, SERCOM_SPI_INTFLAG_TXC | SERCOM_SPI_INTFLAG_DRE))) {
		;
	}
	hri_sercomspi_clear_INTFLAG_reg(hw, SERCOM_SPI_INTFLAG_TXC | SERCOM_SPI_INTFLAG_DRE);
}

/** Holds run time information for message sync transaction. */
struct _spi_trans_ctrl {
	/** Pointer to transmitting data buffer. */
	uint8_t *txbuf;
	/** Pointer to receiving data buffer. */
	uint8_t *rxbuf;
	/** Count number of data transmitted. */
	uint32_t txcnt;
	/** Count number of data received. */
	uint32_t rxcnt;
};

/** Check interrupt flag of RXC and update transaction runtime information. */
static inline bool _spi_rx_check_and_receive(void *const hw, const uint32_t iflag, struct _spi_trans_ctrl *ctrl)
{
	if (!(iflag & SERCOM_SPI_INTFLAG_RXC)) {
		return false;
	}

	uint32_t data = hri_sercomspi_read_DATA_reg(hw);

	if (ctrl->rxbuf) {
		*ctrl->rxbuf++ = (uint8_t)data;
	}

	ctrl->rxcnt++;

	return true;
}

/** Check interrupt flag of DRE and update transaction runtime information. */
static inline void _spi_tx_check_and_send(void *const hw, const uint32_t iflag, struct _spi_trans_ctrl *ctrl,
                                          uint16_t dummy)
{
	if (!(SERCOM_SPI_INTFLAG_DRE & iflag)) {
		return;
	}

	uint32_t data;
	if (ctrl->txbuf) {
		data = *ctrl->txbuf++;
	} else {
		data = dummy;
	}

	ctrl->txcnt++;
	hri_sercomspi_write_DATA_reg(hw, data);
}

/** Check interrupt flag of ERROR and update transaction runtime information. */
static inline int32_t _spi_err_check(const uint32_t iflag, void *const hw)
{
	if (SERCOM_SPI_INTFLAG_ERROR & iflag) {
		hri_sercomspi_clear_STATUS_reg(hw, ~0);
		hri_sercomspi_clear_INTFLAG_reg(hw, SERCOM_SPI_INTFLAG_ERROR);
		return ERR_OVERFLOW;
	}

	return ERR_NONE;
}

int32_t _spi_m_sync_trans(struct _spi_m_sync_dev *dev, const struct spi_xfer *msg)
{
    ASSERT(dev);
    ASSERT(dev->prvt);

	void * hw = dev->prvt;

	/* If settings are not applied (pending), we can not go on */
	if (hri_sercomspi_is_syncing(
	        hw, (SERCOM_SPI_SYNCBUSY_SWRST | SERCOM_SPI_SYNCBUSY_ENABLE | SERCOM_SPI_SYNCBUSY_CTRLB))) {
		return ERR_BUSY;
	}

	/* SPI must be enabled to start synchronous transfer */
	if (!hri_sercomspi_get_CTRLA_ENABLE_bit(hw)) {
		return ERR_NOT_INITIALIZED;
	}

    struct _spi_trans_ctrl ctrl = {msg->txbuf, msg->rxbuf, 0, 0};

	int32_t rc = 0;
	for (;;) {
		uint32_t iflag = hri_sercomspi_read_INTFLAG_reg(hw);

		if (!_spi_rx_check_and_receive(hw, iflag, &ctrl)) {
			/* In master mode, do not start next byte before previous byte received
			 * to make better output waveform */
			if (ctrl.rxcnt >= ctrl.txcnt) {
				_spi_tx_check_and_send(hw, iflag, &ctrl, dev->dummy_byte);
			}
		}

		rc = _spi_err_check(iflag, hw);

		if (rc < 0) {
			break;
		}
		if (ctrl.txcnt >= msg->size && ctrl.rxcnt >= msg->size) {
			rc = ctrl.txcnt;
			break;
		}
	}
	/* Wait until SPI bus idle */
	_spi_wait_bus_idle(hw);

	return rc;
}

int32_t _spi_m_async_enable_tx(struct _spi_async_dev *dev, bool state)
{
    ASSERT(dev);
    ASSERT(dev->prvt);

	if (state) {
		hri_sercomspi_set_INTEN_DRE_bit(dev->prvt);
	} else {
		hri_sercomspi_clear_INTEN_DRE_bit(dev->prvt);
	}

	return ERR_NONE;
}

int32_t _spi_s_async_enable_tx(struct _spi_s_async_dev *dev, bool state)
{
	return _spi_m_async_enable_tx(dev, state);
}

int32_t _spi_m_async_enable_rx(struct _spi_async_dev *dev, bool state)
{
    ASSERT(dev);
    ASSERT(dev->prvt);

	if (state) {
		hri_sercomspi_set_INTEN_RXC_bit(dev->prvt);
	} else {
		hri_sercomspi_clear_INTEN_RXC_bit(dev->prvt);
	}

	return ERR_NONE;
}

int32_t _spi_s_async_enable_rx(struct _spi_s_async_dev *dev, bool state)
{
	return _spi_m_async_enable_rx(dev, state);
}

int32_t _spi_m_async_enable_tx_complete(struct _spi_async_dev *dev, bool state)
{
    ASSERT(dev);
    ASSERT(dev->prvt);

	if (state) {
		hri_sercomspi_set_INTEN_TXC_bit(dev->prvt);
	} else {
		hri_sercomspi_clear_INTEN_TXC_bit(dev->prvt);
	}

	return ERR_NONE;
}

int32_t _spi_s_async_enable_ss_detect(struct _spi_s_async_dev *dev, bool state)
{
	return _spi_m_async_enable_tx_complete(dev, state);
}

int32_t _spi_m_async_write_one(struct _spi_async_dev *dev, uint16_t data)
{
    ASSERT(dev);
    ASSERT(dev->prvt);

	hri_sercomspi_write_DATA_reg(dev->prvt, data);

	return ERR_NONE;
}

int32_t _spi_s_async_write_one(struct _spi_s_async_dev *dev, uint16_t data)
{
    ASSERT(dev);
    ASSERT(dev->prvt);

	hri_sercomspi_write_DATA_reg(dev->prvt, data);

	return ERR_NONE;
}

int32_t _spi_s_sync_write_one(struct _spi_s_sync_dev *dev, uint16_t data)
{
    ASSERT(dev);
    ASSERT(dev->prvt);

	hri_sercomspi_write_DATA_reg(dev->prvt, data);

	return ERR_NONE;
}

uint16_t _spi_m_async_read_one(struct _spi_async_dev *dev)
{
    ASSERT(dev);
    ASSERT(dev->prvt);

	return hri_sercomspi_read_DATA_reg(dev->prvt);
}

uint16_t _spi_s_async_read_one(struct _spi_s_async_dev *dev)
{
    ASSERT(dev);
    ASSERT(dev->prvt);

	return hri_sercomspi_read_DATA_reg(dev->prvt);
}

uint16_t _spi_s_sync_read_one(struct _spi_s_sync_dev *dev)
{
    ASSERT(dev);
    ASSERT(dev->prvt);

	return hri_sercomspi_read_DATA_reg(dev->prvt);
}

int32_t _spi_m_async_register_callback(struct _spi_async_dev *dev, const enum _spi_async_dev_cb_type cb_type,
                                       const FUNC_PTR func)
{
    ASSERT(dev);
    ASSERT(cb_type < SPI_DEV_CB_N);

    FUNC_PTR *p_ls  = (FUNC_PTR *)&dev->callbacks;
    p_ls[cb_type] = (FUNC_PTR)func;

    return ERR_NONE;
}

int32_t _spi_s_async_register_callback(struct _spi_s_async_dev *dev, const enum _spi_s_async_dev_cb_type cb_type,
                                       const FUNC_PTR func)
{
	return _spi_m_async_register_callback(dev, cb_type, func);
}

bool _spi_s_sync_is_tx_ready(struct _spi_s_sync_dev *dev)
{
    ASSERT(dev);
    ASSERT(dev->prvt);

	return hri_sercomi2cm_get_INTFLAG_reg(dev->prvt, SERCOM_SPI_INTFLAG_DRE);
}

bool _spi_s_sync_is_rx_ready(struct _spi_s_sync_dev *dev)
{
    ASSERT(dev);
    ASSERT(dev->prvt);

	return hri_sercomi2cm_get_INTFLAG_reg(dev->prvt, SERCOM_SPI_INTFLAG_RXC);
}

bool _spi_s_sync_is_ss_deactivated(struct _spi_s_sync_dev *dev)
{
    ASSERT(dev);
    ASSERT(dev->prvt);

    void *hw = dev->prvt;

	if (hri_sercomi2cm_get_INTFLAG_reg(hw, SERCOM_SPI_INTFLAG_TXC)) {
		hri_sercomspi_clear_INTFLAG_reg(hw, SERCOM_SPI_INTFLAG_TXC);
		return true;
	}
	return false;
}

bool _spi_s_sync_is_error(struct _spi_s_sync_dev *dev)
{
    ASSERT(dev);
    ASSERT(dev->prvt);
    void *hw = dev->prvt;

	if (hri_sercomi2cm_get_INTFLAG_reg(hw, SERCOM_SPI_INTFLAG_ERROR)) {
		hri_sercomspi_clear_STATUS_reg(hw, SERCOM_SPI_STATUS_BUFOVF);
		hri_sercomspi_clear_INTFLAG_reg(hw, SERCOM_SPI_INTFLAG_ERROR);
		return true;
	}
	return false;
}

/**
 * \brief Enable/disable SPI master interrupt
 *
 * param[in] device The pointer to SPI master device instance
 * param[in] type The type of interrupt to disable/enable if applicable
 * param[in] state Enable or disable
 */
void _spi_m_async_set_irq_state(struct _spi_async_dev *const device, const enum _spi_async_dev_cb_type type,
                                const bool state)
{
	ASSERT(device);

	if (SPI_DEV_CB_ERROR == type) {
		hri_sercomspi_write_INTEN_ERROR_bit(device->prvt, state);
	}
}

/**
 * \brief Enable/disable SPI slave interrupt
 *
 * param[in] device The pointer to SPI slave device instance
 * param[in] type The type of interrupt to disable/enable if applicable
 * param[in] state Enable or disable
 */
void _spi_s_async_set_irq_state(struct _spi_async_dev *const device, const enum _spi_async_dev_cb_type type,
                                const bool state)
{
	_spi_m_async_set_irq_state(device, type, state);
}

#ifndef CONF_SERCOM_2_SPI_M_DMA_TX_CHANNEL
#define CONF_SERCOM_2_SPI_M_DMA_TX_CHANNEL 0
#endif
#ifndef CONF_SERCOM_2_SPI_M_DMA_RX_CHANNEL
#define CONF_SERCOM_2_SPI_M_DMA_RX_CHANNEL 1
#endif
#ifndef CONF_SERCOM_4_SPI_M_DMA_TX_CHANNEL
#define CONF_SERCOM_4_SPI_M_DMA_TX_CHANNEL 0
#endif
#ifndef CONF_SERCOM_4_SPI_M_DMA_RX_CHANNEL
#define CONF_SERCOM_4_SPI_M_DMA_RX_CHANNEL 1
#endif
#ifndef CONF_SERCOM_5_SPI_M_DMA_TX_CHANNEL
#define CONF_SERCOM_5_SPI_M_DMA_TX_CHANNEL 0
#endif
#ifndef CONF_SERCOM_5_SPI_M_DMA_RX_CHANNEL
#define CONF_SERCOM_5_SPI_M_DMA_RX_CHANNEL 1
#endif
#ifndef CONF_SERCOM_7_SPI_M_DMA_TX_CHANNEL
#define CONF_SERCOM_7_SPI_M_DMA_TX_CHANNEL 0
#endif
#ifndef CONF_SERCOM_7_SPI_M_DMA_RX_CHANNEL
#define CONF_SERCOM_7_SPI_M_DMA_RX_CHANNEL 1
#endif
/** \internal Enable SERCOM SPI RX
 *
 *  \param[in] hw Pointer to the hardware register base.
 *
 * \return Enabling status
 */
static int32_t _spi_sync_rx_enable(void *const hw)
{
	if (hri_sercomspi_is_syncing(hw, SERCOM_SPI_SYNCBUSY_CTRLB)) {
		return ERR_BUSY;
	}

	hri_sercomspi_set_CTRLB_RXEN_bit(hw);

	return ERR_NONE;
}

/** \internal Disable SERCOM SPI RX
 *
 *  \param[in] hw Pointer to the hardware register base.
 *
 * \return Disabling status
 */
static int32_t _spi_sync_rx_disable(void *const hw)
{
	if (hri_sercomspi_is_syncing(hw, SERCOM_SPI_SYNCBUSY_CTRLB)) {
		return ERR_BUSY;
	}
	hri_sercomspi_clear_CTRLB_RXEN_bit(hw);

	return ERR_NONE;
}

static int32_t _spi_m_dma_rx_enable(struct _spi_m_dma_dev *dev)
{
	return _spi_sync_rx_enable(dev->prvt);
}

static int32_t _spi_m_dma_rx_disable(struct _spi_m_dma_dev *dev)
{
	return _spi_sync_rx_disable(dev->prvt);
}

/**
 *  \brief Get the spi source address for DMA
 *  \param[in] dev Pointer to the SPI device instance
 *
 *  \return The spi source address
 */
static uint32_t _spi_m_get_source_for_dma(void *const hw)
{
	return (uint32_t) & (((Sercom *)hw)->SPI.DATA);
}

/**
 *  \brief Get the spi destination address for DMA
 *  \param[in] dev Pointer to the SPI device instance
 *
 *  \return The spi destination address
 */
static uint32_t _spi_m_get_destination_for_dma(void *const hw)
{
	return (uint32_t) & (((Sercom *)hw)->SPI.DATA);
}

/**
 *  \brief Return the SPI TX DMA channel index
 *  \param[in] hw_addr The hardware register base address
 *
 *  \return SPI TX DMA channel index.
 */
static uint8_t _spi_get_tx_dma_channel(const void *const hw)
{
	int8_t index = _sercom_get_hardware_index(hw);

	switch (index) {
	case 2:
		return CONF_SERCOM_2_SPI_M_DMA_TX_CHANNEL;
	case 4:
		return CONF_SERCOM_4_SPI_M_DMA_TX_CHANNEL;
	case 5:
		return CONF_SERCOM_5_SPI_M_DMA_TX_CHANNEL;
	case 7:
		return CONF_SERCOM_7_SPI_M_DMA_TX_CHANNEL;
	default:
        ASSERT(0);
		return 0;
	}
}

/**
 *  \brief Return the SPI RX DMA channel index
 *  \param[in] hw_addr The hardware register base address
 *
 *  \return SPI RX DMA channel index.
 */
static uint8_t _spi_get_rx_dma_channel(const void *const hw)
{
	int8_t index = _sercom_get_hardware_index(hw);

	switch (index) {
	case 2:
		return CONF_SERCOM_2_SPI_M_DMA_RX_CHANNEL;
	case 4:
		return CONF_SERCOM_4_SPI_M_DMA_RX_CHANNEL;
	case 5:
		return CONF_SERCOM_5_SPI_M_DMA_RX_CHANNEL;
	case 7:
		return CONF_SERCOM_7_SPI_M_DMA_RX_CHANNEL;
	default:
        ASSERT(0);
		return 0;
	}
}

/**
 *  \brief Callback for RX
 *  \param[in, out] dev Pointer to the DMA resource.
 */
static void _spi_dma_rx_complete(struct _dma_resource *resource)
{
	struct _spi_m_dma_dev *dev = (struct _spi_m_dma_dev *)resource->back;

	if (dev->callbacks.rx) {
		dev->callbacks.rx(resource);
	}
}

/**
 *  \brief Callback for TX
 *  \param[in, out] dev Pointer to the DMA resource.
 */
static void _spi_dma_tx_complete(struct _dma_resource *resource)
{
	struct _spi_m_dma_dev *dev = (struct _spi_m_dma_dev *)resource->back;

	if (dev->callbacks.tx) {
		dev->callbacks.tx(resource);
	}
}

/**
 *  \brief Callback for ERROR
 *  \param[in, out] dev Pointer to the DMA resource.
 */
static void _spi_dma_error_occured(struct _dma_resource *resource)
{
	struct _spi_m_dma_dev *dev = (struct _spi_m_dma_dev *)resource->back;

	if (dev->callbacks.error) {
		dev->callbacks.error(resource);
	}
}

int32_t _spi_m_dma_init(struct _spi_m_dma_dev *dev, void *const hw)
{
	const struct sercomspi_regs_cfg *regs = _spi_get_regs((uint32_t)hw);

    ASSERT(dev);
    ASSERT(hw);

	if (regs == NULL) {
        ASSERT(0);
		return ERR_INVALID_ARG;
	}

	if (!hri_sercomspi_is_syncing(hw, SERCOM_SPI_SYNCBUSY_SWRST)) {
		uint32_t mode = regs->ctrla & SERCOM_SPI_CTRLA_MODE_Msk;
		if (hri_sercomspi_get_CTRLA_reg(hw, SERCOM_SPI_CTRLA_ENABLE)) {
			hri_sercomspi_clear_CTRLA_ENABLE_bit(hw);
			hri_sercomspi_wait_for_sync(hw, SERCOM_SPI_SYNCBUSY_ENABLE);
		}
		hri_sercomspi_write_CTRLA_reg(hw, SERCOM_SPI_CTRLA_SWRST | mode);
	}
	hri_sercomspi_wait_for_sync(hw, SERCOM_SPI_SYNCBUSY_SWRST);

	dev->prvt = hw;

	_spi_load_regs_master(hw, regs);

	/* Initialize DMA rx channel */
	_dma_get_channel_resource(&dev->resource, _spi_get_rx_dma_channel(hw));
	dev->resource->back                 = dev;
	dev->resource->dma_cb.transfer_done = _spi_dma_rx_complete;
	dev->resource->dma_cb.error         = _spi_dma_error_occured;
	/* Initialize DMA tx channel */
	_dma_get_channel_resource(&dev->resource, _spi_get_tx_dma_channel(hw));
	dev->resource->back                 = dev;
	dev->resource->dma_cb.transfer_done = _spi_dma_tx_complete;
	dev->resource->dma_cb.error         = _spi_dma_error_occured;

	return ERR_NONE;
}

int32_t _spi_m_dma_deinit(struct _spi_m_dma_dev *dev)
{
    ASSERT(dev);
    ASSERT(dev->prvt);

	return _spi_deinit(dev->prvt);
}

int32_t _spi_m_dma_enable(struct _spi_m_dma_dev *dev)
{
    ASSERT(dev);
    ASSERT(dev->prvt);

	return _spi_sync_enable(dev->prvt);
}

int32_t _spi_m_dma_disable(struct _spi_m_dma_dev *dev)
{
    ASSERT(dev);
    ASSERT(dev->prvt);

	return _spi_sync_disable(dev->prvt);
}

int32_t _spi_m_dma_set_mode(struct _spi_m_dma_dev *dev, const enum spi_transfer_mode mode)
{
    ASSERT(dev);
    ASSERT(dev->prvt);

	return _spi_set_mode(dev->prvt, mode);
}

int32_t _spi_m_dma_set_baudrate(struct _spi_m_dma_dev *dev, const uint32_t baud_val)
{
    ASSERT(dev);
    ASSERT(dev->prvt);

	return _spi_set_baudrate(dev->prvt, baud_val);
}

int32_t _spi_m_dma_set_data_order(struct _spi_m_dma_dev *dev, const enum spi_data_order dord)
{
    ASSERT(dev);
    ASSERT(dev->prvt);

	return _spi_set_data_order(dev->prvt, dord);
}

void _spi_m_dma_register_callback(struct _spi_m_dma_dev *dev, enum _spi_dma_dev_cb_type type, _spi_dma_cb_t func)
{
	switch (type) {
	case SPI_DEV_CB_DMA_TX:
		dev->callbacks.tx = func;
		_dma_set_irq_state(_spi_get_tx_dma_channel(dev->prvt), DMA_TRANSFER_COMPLETE_CB, func != NULL);
		break;
	case SPI_DEV_CB_DMA_RX:
		dev->callbacks.rx = func;
		_dma_set_irq_state(_spi_get_rx_dma_channel(dev->prvt), DMA_TRANSFER_COMPLETE_CB, func != NULL);
		break;
	case SPI_DEV_CB_DMA_ERROR:
		dev->callbacks.error = func;
		_dma_set_irq_state(_spi_get_rx_dma_channel(dev->prvt), DMA_TRANSFER_ERROR_CB, func != NULL);
		_dma_set_irq_state(_spi_get_tx_dma_channel(dev->prvt), DMA_TRANSFER_ERROR_CB, func != NULL);
		break;
    default:
	case SPI_DEV_CB_DMA_N:
        ASSERT(0);
		break;
	}
}

int32_t _spi_m_dma_transfer(struct _spi_m_dma_dev *dev, uint8_t const *txbuf, uint8_t *const rxbuf,
                            const uint16_t length)
{
    ASSERT(dev);
    ASSERT(dev->prvt);

	const struct sercomspi_regs_cfg *regs  = _spi_get_regs((uint32_t)dev->prvt);
	uint8_t                          rx_ch = _spi_get_rx_dma_channel(dev->prvt);
	uint8_t                          tx_ch = _spi_get_tx_dma_channel(dev->prvt);

	if (rxbuf) {
		/* Enable spi rx */
		_spi_m_dma_rx_enable(dev);
		_dma_set_source_address(rx_ch, (void *)_spi_m_get_source_for_dma(dev->prvt));
		_dma_set_destination_address(rx_ch, rxbuf);
		_dma_set_data_amount(rx_ch, length);
		_dma_enable_transaction(rx_ch, false);
	} else {
		/* Disable spi rx */
		_spi_m_dma_rx_disable(dev);
	}

	if (txbuf) {
		/* Enable spi tx */
		_dma_set_source_address(tx_ch, txbuf);
		_dma_set_destination_address(tx_ch, (void *)_spi_m_get_destination_for_dma(dev->prvt));
		_dma_srcinc_enable(tx_ch, true);
		_dma_set_data_amount(tx_ch, length);
	} else {
		_dma_set_source_address(tx_ch, &regs->dummy_byte);
		_dma_set_destination_address(tx_ch, (void *)_spi_m_get_destination_for_dma(dev->prvt));
		_dma_srcinc_enable(tx_ch, false);
		_dma_set_data_amount(tx_ch, length);
	}
	_dma_enable_transaction(tx_ch, false);

	return ERR_NONE;
}

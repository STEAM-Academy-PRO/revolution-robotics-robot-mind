/*
 * imu_ll.c
 *
 * Created: 2019. 08. 12. 18:23:22
 *  Author: Dániel Buga
 */ 
 
#include "imu_ll.h"

#include "rrrc_hal.h"
#include <hal_spi_m_dma.h>

static struct spi_m_sync_descriptor spi;

static inline void _imu_send_write_address(uint8_t addr)
{
    uint8_t address = addr & 0x7Fu;

    struct spi_xfer xfer;

    xfer.txbuf = &address;
    xfer.rxbuf = NULL;
    xfer.size = 1u;
    
    spi_m_sync_transfer(&spi, &xfer);
}

static inline void _imu_send_read_address(uint8_t addr)
{
    uint8_t address = 0x80u | (addr & 0x7Fu);

    struct spi_xfer xfer;

    xfer.txbuf = &address;
    xfer.rxbuf = NULL;
    xfer.size = 1u;
    
    spi_m_sync_transfer(&spi, &xfer);
}

void _imu_write_registers(uint8_t reg, uint8_t* pData, size_t data_count)
{
    struct spi_xfer xfer;

    xfer.txbuf = pData;
    xfer.rxbuf = NULL;
    xfer.size = data_count;
    
    gpio_set_pin_level(IMU_CS_pin, false);
    _imu_send_write_address(reg);
    spi_m_sync_transfer(&spi, &xfer);
    gpio_set_pin_level(IMU_CS_pin, true);
}

void _imu_read_registers(uint8_t reg, uint8_t* pData, size_t data_count)
{
    struct spi_xfer xfer;

    xfer.txbuf = NULL;
    xfer.rxbuf = pData;
    xfer.size = data_count;
    
    gpio_set_pin_level(IMU_CS_pin, false);
    _imu_send_read_address(reg);
    spi_m_sync_transfer(&spi, &xfer);
    gpio_set_pin_level(IMU_CS_pin, true);
}

void _imu_write_register(uint8_t reg, uint8_t data)
{
    struct spi_xfer xfer;
    
    uint8_t address = reg & 0x7Fu;
    uint8_t buffer[] = {address, data};

    xfer.txbuf = buffer;
    xfer.rxbuf = NULL;
    xfer.size = 2u;
    
    gpio_set_pin_level(IMU_CS_pin, false);
    spi_m_sync_transfer(&spi, &xfer);
    gpio_set_pin_level(IMU_CS_pin, true);
}

uint8_t _imu_read_register(uint8_t reg)
{
    struct spi_xfer xfer;
    
    uint8_t address = 0x80u | (reg & 0x7Fu);
    uint8_t txBuffer[] = {address, 0xFFu};
    uint8_t rxBuffer[2];

    xfer.txbuf = txBuffer;
    xfer.rxbuf = rxBuffer;
    xfer.size = 2u;
    
    gpio_set_pin_level(IMU_CS_pin, false);
    spi_m_sync_transfer(&spi, &xfer);
    gpio_set_pin_level(IMU_CS_pin, true);

    return rxBuffer[1];
}

bool imu_axl_data_ready(void)
{
    return gpio_get_pin_level(IMU_INT1_pin);
}

bool imu_gyro_data_ready(void)
{
    return gpio_get_pin_level(IMU_INT2_pin);
}

void IMU_Call_LowLevelInit(void)
{
    hri_gclk_write_PCHCTRL_reg(GCLK, SERCOM5_GCLK_ID_CORE, CONF_GCLK_SERCOM5_CORE_SRC | (1 << GCLK_PCHCTRL_CHEN_Pos));
    hri_gclk_write_PCHCTRL_reg(GCLK, SERCOM5_GCLK_ID_SLOW, CONF_GCLK_SERCOM5_SLOW_SRC | (1 << GCLK_PCHCTRL_CHEN_Pos));
    hri_mclk_set_APBDMASK_SERCOM5_bit(MCLK);

    gpio_set_pin_level(IMU_MOSI_pin, false);
    gpio_set_pin_direction(IMU_MOSI_pin, GPIO_DIRECTION_OUT);
    gpio_set_pin_function(IMU_MOSI_pin, IMU_MOSI_pin_function);

    gpio_set_pin_level(IMU_SCLK_pin, false);
    gpio_set_pin_direction(IMU_SCLK_pin, GPIO_DIRECTION_OUT);
    gpio_set_pin_function(IMU_SCLK_pin, IMU_SCLK_pin_function);

    gpio_set_pin_direction(IMU_MISO_pin, GPIO_DIRECTION_IN);
    gpio_set_pin_pull_mode(IMU_MISO_pin, GPIO_PULL_OFF);
    gpio_set_pin_function(IMU_MISO_pin, IMU_MISO_pin_function);

    gpio_set_pin_direction(IMU_INT1_pin, GPIO_DIRECTION_IN);
    gpio_set_pin_pull_mode(IMU_INT1_pin, GPIO_PULL_OFF);
    gpio_set_pin_function(IMU_INT1_pin, GPIO_PIN_FUNCTION_OFF);

    gpio_set_pin_direction(IMU_INT2_pin, GPIO_DIRECTION_IN);
    gpio_set_pin_pull_mode(IMU_INT2_pin, GPIO_PULL_OFF);
    gpio_set_pin_function(IMU_INT2_pin, GPIO_PIN_FUNCTION_OFF);

    /* CS permanently tied to ground */
    gpio_set_pin_level(IMU_CS_pin, true);
    gpio_set_pin_direction(IMU_CS_pin, GPIO_DIRECTION_OUT);
    gpio_set_pin_function(IMU_CS_pin, IMU_CS_pin_function);

    spi_m_sync_init(&spi, IMU_SERCOM);
    spi_m_sync_enable(&spi);
}

#include "i2cHal.h"
#include "utils_assert.h"

/* The MCU will transmit this buffer back when empty */
static const uint8_t empty_tx_buffer[] = { 0xFFu };

/* TODO: this file should not know about protocol specifics like these */
#define PACKET_HEADER_SIZE  6u
#define MAX_RX_PAYLOAD      255u
#define RX_BUFFER_CAPACITY (PACKET_HEADER_SIZE + MAX_RX_PAYLOAD)

typedef struct
{
    struct _i2c_s_async_device device;

    const uint8_t* txBuffer;
    const uint8_t* txBufferEnd;

    const uint8_t*  nextTxBuffer;
    const uint8_t*  nextTxBufferEnd;

    uint8_t         rxBuffer[RX_BUFFER_CAPACITY];
    uint16_t        rxBufferCount;
} i2c_hal_descriptor;

/* Interrupt handler declarations. TX/RX from the MCU's perspective */
static void i2c_hal_on_address_matched(const uint8_t dir);
static void i2c_hal_on_error(void);
static void i2c_hal_on_stop_tx(const uint8_t dir);
static void i2c_hal_on_stop_rx(const uint8_t dir);

static i2c_hal_descriptor descriptor;

int32_t i2c_hal_init(void* hw, uint8_t address)
{
    i2cs_config_t config = {
        .hw = hw,
        .ctrl_a = SERCOM_I2CM_CTRLA_MODE(0x04u)
                | (1u << SERCOM_I2CS_CTRLA_RUNSTDBY_Pos)
                | SERCOM_I2CS_CTRLA_SDAHOLD(0u)
                | (0u << SERCOM_I2CS_CTRLA_SEXTTOEN_Pos)
                | (0u << SERCOM_I2CS_CTRLA_SPEED_Pos)
                | (0u << SERCOM_I2CS_CTRLA_SCLSM_Pos)
                | (0u << SERCOM_I2CS_CTRLA_LOWTOUTEN_Pos),
        .ctrl_b = (1u << SERCOM_I2CS_CTRLB_SMEN_Pos)
                | (0u << SERCOM_I2CS_CTRLB_GCMD_Pos)
                | (0u << SERCOM_I2CS_CTRLB_AACKEN_Pos)
                | SERCOM_I2CS_CTRLB_CMD(0u)
                | (0u << SERCOM_I2CS_CTRLB_ACKACT_Pos)
                | SERCOM_I2CS_CTRLB_AMODE(0u),
        .address = (0u << SERCOM_I2CS_ADDR_GENCEN_Pos)
                 | (0u << SERCOM_I2CS_ADDR_TENBITEN_Pos)
                 | SERCOM_I2CS_ADDR_ADDRMASK(0u)
                 | SERCOM_I2CS_ADDR_ADDR(address)
    };
    int32_t result = _i2c_s_async_init(&descriptor.device, &config);

    if (result == ERR_NONE)
    {
        descriptor.nextTxBuffer = empty_tx_buffer;
        descriptor.nextTxBufferEnd = empty_tx_buffer;

        descriptor.txBuffer = empty_tx_buffer;
        descriptor.txBufferEnd = empty_tx_buffer;

        descriptor.rxBufferCount = 0u;

        descriptor.device.cb.addrm_cb   = &i2c_hal_on_address_matched;
        descriptor.device.cb.error_cb   = &i2c_hal_on_error;
        /* will be overwritten in address match handler but we need a non-NULL value */
        descriptor.device.cb.stop_cb    = &i2c_hal_on_stop_rx;

        hri_sercomi2cs_set_INTEN_ERROR_bit(descriptor.device.hw);
        hri_sercomi2cs_set_INTEN_AMATCH_bit(descriptor.device.hw);
        hri_sercomi2cs_set_INTEN_PREC_bit(descriptor.device.hw);
        hri_sercomi2cs_set_INTEN_DRDY_bit(descriptor.device.hw);

        result = _i2c_s_async_enable(&descriptor.device);
    }

    return result;
}

void i2c_hal_receive(void)
{
    /* set size to 0 to avoid needing a critical section */
    descriptor.rxBufferCount = 0u;
}

void i2c_hal_set_tx_buffer(const uint8_t* buffer, size_t bufferSize)
{
    const uint8_t* bufferEnd;
    if (bufferSize == 0u)
    {
        buffer = empty_tx_buffer;
        bufferEnd = empty_tx_buffer;
    }
    else
    {
        bufferEnd = buffer + bufferSize - 1;
    }

    uint32_t primask = __get_PRIMASK();
    __disable_irq();
    descriptor.nextTxBuffer = buffer;
    descriptor.nextTxBufferEnd = bufferEnd;
    __set_PRIMASK(primask);
}

/* interrupt handlers */
static void i2c_hal_on_address_matched(const uint8_t dir)
{
    /* Direction bit values from the MCU's perspective */
    #define I2C_DIR_RX  0u
    #define I2C_DIR_TX  1u

    if (dir == I2C_DIR_RX)
    {
        i2c_hal_rx_started();
        descriptor.device.cb.stop_cb = &i2c_hal_on_stop_rx;
    }
    else
    {
        descriptor.txBuffer = descriptor.nextTxBuffer;
        descriptor.txBufferEnd = descriptor.nextTxBufferEnd;
        descriptor.device.cb.stop_cb = &i2c_hal_on_stop_tx;
    }
}

static void i2c_hal_on_error(void)
{
    i2c_hal_error_occurred();
}

void sercom2_rx_done_cb(uint8_t data)
{
    if (descriptor.rxBufferCount < sizeof(descriptor.rxBuffer))
    {
        descriptor.rxBuffer[descriptor.rxBufferCount] = data;
    }

    ++descriptor.rxBufferCount;
}

void sercom2_tx_cb(void)
{
    uint8_t byte = *descriptor.txBuffer;
    _i2c_s_async_write_byte(&descriptor.device, byte);

    if (descriptor.txBuffer != descriptor.txBufferEnd)
    {
        ++descriptor.txBuffer;
    }
}

static void i2c_hal_on_stop_rx(const uint8_t dir)
{
    (void) dir;
    i2c_hal_rx_complete(descriptor.rxBuffer, sizeof(descriptor.rxBuffer), descriptor.rxBufferCount);
}

static void i2c_hal_on_stop_tx(const uint8_t dir)
{
    (void) dir;
    i2c_hal_tx_complete();
}

__attribute__((weak))
void i2c_hal_rx_started(void)
{
}

__attribute__((weak))
void i2c_hal_rx_complete(const uint8_t* buffer, size_t bufferSize, size_t bytesReceived)
{
    (void) buffer;
    (void) bufferSize;
    (void) bytesReceived;
}

__attribute__((weak))
void i2c_hal_tx_complete(void)
{
}

__attribute__((weak))
void i2c_hal_error_occurred(void)
{
}

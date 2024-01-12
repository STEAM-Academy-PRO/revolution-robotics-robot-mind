/*
 * i2cHal.c
 *
 * Created: 07/05/2019 11:42:39
 *  Author: Dániel Buga
 */ 

#include "i2cHal.h"
#include "utils_assert.h"

#define I2C_DIR_MASTER_TX  0u
#define I2C_DIR_MASTER_RX  1u

static void i2c_hal_on_address_matched(struct _i2c_s_async_device *const device, const uint8_t dir);
static void i2c_hal_on_error(struct _i2c_s_async_device *const device);
static void i2c_hal_on_rx_done(struct _i2c_s_async_device *const device, const uint8_t data);
static void i2c_hal_on_tx(struct _i2c_s_async_device *const device);
static void i2c_hal_on_stop(struct _i2c_s_async_device *const device, const uint8_t dir);

int32_t i2c_hal_init(i2c_hal_descriptor* descr, void* hw)
{
    ASSERT(descr && hw );

    int32_t result = _i2c_s_async_init(&descr->device, hw);

    if (result == ERR_NONE)
    {
        descr->nextTxBuffer = NULL;
        descr->nextTxBufferSize = 0u;
        
        descr->txBuffer = NULL;
        descr->txBufferSize = 0u;
        descr->txBufferIndex = 0u;

        descr->rxBuffer = NULL;
        descr->rxBufferSize = 0u;
        descr->rxBufferCount = 0u;

        result = _i2c_s_async_enable(&descr->device);
        if (result == ERR_NONE)
        {
            descr->device.cb.addrm_cb   = &i2c_hal_on_address_matched;
            descr->device.cb.error_cb   = &i2c_hal_on_error;
            descr->device.cb.rx_done_cb = &i2c_hal_on_rx_done;
            descr->device.cb.tx_cb      = &i2c_hal_on_tx;
            descr->device.cb.stop_cb    = &i2c_hal_on_stop;

            hri_sercomi2cs_set_INTEN_ERROR_bit(descr->device.hw);
            hri_sercomi2cs_set_INTEN_AMATCH_bit(descr->device.hw);
            hri_sercomi2cs_set_INTEN_PREC_bit(descr->device.hw);
            hri_sercomi2cs_set_INTEN_DRDY_bit(descr->device.hw);
        }
    }

    return result;
}

void i2c_hal_receive(i2c_hal_descriptor* descr, uint8_t* buffer, size_t bufferSize)
{
    /* set size to 0 to avoid needing a critical section */
    descr->rxBufferSize = 0u;
    descr->rxBuffer = buffer;
    descr->rxBufferCount = 0u;
    descr->rxBufferSize = bufferSize;
}

void i2c_hal_set_tx_buffer(i2c_hal_descriptor* descr, const uint8_t* buffer, size_t bufferSize)
{
    /* set size to 0 to avoid needing a critical section */
    descr->nextTxBufferSize = 0u;
    descr->nextTxBuffer = buffer;
    descr->nextTxBufferSize = bufferSize;
}

__attribute__((weak))
void i2c_hal_rx_started(i2c_hal_descriptor* descr)
{

}

__attribute__((weak))
void i2c_hal_rx_complete(i2c_hal_descriptor* descr, const uint8_t* buffer, size_t bufferSize, size_t bytesReceived)
{

}

__attribute__((weak))
void i2c_hal_tx_complete(i2c_hal_descriptor* descr)
{

}

/* interrupt handlers */
static void i2c_hal_on_address_matched(struct _i2c_s_async_device *const device, const uint8_t dir)
{
    i2c_hal_descriptor *descr = CONTAINER_OF(device, i2c_hal_descriptor, device);
    if (dir == I2C_DIR_MASTER_TX)
    {
        descr->rxBufferCount = 0u;
        i2c_hal_rx_started(descr);
    }
    else
    {
        descr->txBuffer = descr->nextTxBuffer;
        descr->txBufferSize = descr->nextTxBufferSize;
        descr->txBufferIndex = 0u;
    }
}

static void i2c_hal_on_error(struct _i2c_s_async_device *const device)
{
    /* ignore for now */
}

static void i2c_hal_on_rx_done(struct _i2c_s_async_device *const device, const uint8_t data)
{
    i2c_hal_descriptor *descr = CONTAINER_OF(device, i2c_hal_descriptor, device);

    if (descr->rxBufferCount < descr->rxBufferSize)
    {
        descr->rxBuffer[descr->rxBufferCount] = data;
    }
    
    ++descr->rxBufferCount;
}

static void i2c_hal_on_tx(struct _i2c_s_async_device *const device)
{
    i2c_hal_descriptor *descr = CONTAINER_OF(device, i2c_hal_descriptor, device);

    if (descr->txBufferSize == 0u)
    {
        /* TODO ??? maybe wait for data? */
        _i2c_s_async_write_byte(device, 0xFFu);
    }
    else
    {
        uint8_t byte = descr->txBuffer[descr->txBufferIndex];
        _i2c_s_async_write_byte(device, byte);

        if (descr->txBufferIndex == descr->txBufferSize - 1u)
        {
            descr->txBufferIndex = 0u;
        }
        else
        {
            ++descr->txBufferIndex;
        }
    }
}

static void i2c_hal_on_stop(struct _i2c_s_async_device *const device, const uint8_t dir)
{
    i2c_hal_descriptor *descr = CONTAINER_OF(device, i2c_hal_descriptor, device);
    if (dir == I2C_DIR_MASTER_TX)
    {
        i2c_hal_rx_complete(descr, descr->rxBuffer, descr->rxBufferSize, descr->rxBufferCount);
    }
    else
    {
        i2c_hal_tx_complete(descr);
    }
}

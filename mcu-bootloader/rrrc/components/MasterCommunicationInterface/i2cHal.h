/*
 * i2cHal.h
 *
 * Created: 07/05/2019 11:43:01
 *  Author: Dániel Buga
 */ 


#ifndef I2C_HAL_H_
#define I2C_HAL_H_

#include <hpl_i2c_s_async.h>
#include <stdio.h>

typedef struct
{
    struct _i2c_s_async_device device;

    uint8_t* txBuffer;
    size_t   txBufferSize;
    size_t   txBufferIndex;

    uint8_t* nextTxBuffer;
    volatile size_t nextTxBufferSize;

    uint8_t*        rxBuffer;
    volatile size_t rxBufferSize;
    size_t          rxBufferCount;
} i2c_hal_descriptor;

int32_t i2c_hal_init(i2c_hal_descriptor* descr, void* hw);
void i2c_hal_receive(i2c_hal_descriptor* descr, uint8_t* buffer, size_t bufferSize);
void i2c_hal_set_tx_buffer(i2c_hal_descriptor* descr, const uint8_t* buffer, size_t bufferSize);

void i2c_hal_rx_started(i2c_hal_descriptor* descr);
void i2c_hal_rx_complete(i2c_hal_descriptor* descr, const uint8_t* buffer, size_t bufferSize, size_t bytesReceived);
void i2c_hal_tx_complete(i2c_hal_descriptor* descr);

#endif /* I2CHAL_H_ */

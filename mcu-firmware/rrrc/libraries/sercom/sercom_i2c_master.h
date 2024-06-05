#ifndef SERCOM_I2C_MASTER_H_
#define SERCOM_I2C_MASTER_H_

#include "sercom_base.h"
#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>

typedef struct {
    void* hw;
    uint32_t clock_frequency;
    uint16_t trise; /**< Rise time in ns */
} I2CMasterConfig_t;

typedef enum {
    I2CTransaction_None,
    I2CTransaction_Read,
    I2CTransaction_Write
} I2CTransactionType_t;

struct __I2CMasterInstance_t;

typedef void (*I2CTransactionCallback_t)(struct __I2CMasterInstance_t* instance, size_t transferred);

typedef struct {
    uint8_t slave_addr;
    I2CTransactionType_t type;
    uint8_t* buffer;
    size_t count;
    I2CTransactionCallback_t callback;
} I2CTransaction_t;

typedef struct __I2CMasterInstance_t {
    void* hw;
    bool in_handler;
    I2CTransaction_t current_transaction;
    size_t current_transfer_count;
    bool continue_transaction; /** < false to send a stop condition */
} I2CMasterInstance_t;

typedef enum {
    I2CResult_Ok,
    I2CResult_Busy,
    I2CResult_Error
} I2CResult_t;

I2CResult_t sercom_i2c_master_init(I2CMasterInstance_t* instance, const I2CMasterConfig_t* config);
I2CResult_t sercom_i2c_master_enable(I2CMasterInstance_t* instance);
I2CResult_t sercom_i2c_master_deinit(I2CMasterInstance_t* instance);

I2CResult_t sercom_i2c_master_transfer(I2CMasterInstance_t* instance, const I2CTransaction_t* transaction);
I2CResult_t sercom_i2c_master_continue_read(I2CMasterInstance_t* instance, uint8_t* buffer, size_t size, I2CTransactionCallback_t callback, bool continue_transaction);
I2CResult_t sercom_i2c_master_continue_write(I2CMasterInstance_t* instance, uint8_t* buffer, size_t count, I2CTransactionCallback_t callback, bool continue_transaction);

#endif /* SERCOM_I2C_MASTER_H_ */

#include "SensorPort_I2C.h"
#include <hal_gpio.h>
#include <string.h>

SensorPort_I2C_Status_t SensorPort_I2C_Enable(SensorPort_t* port, uint32_t baudrate)
{
    ASSERT(port->interfaceType == SensorPortComm_None);

    I2CMasterConfig_t config = {
        .hw = port->comm_hw,
        .clock_frequency = baudrate,
        .trise = 215u
    };

    if (sercom_i2c_master_init(&port->sercom.i2cm.sercom_instance, &config) == I2CResult_Ok)
    {
        gpio_set_pin_pull_mode(port->comm_pin0.pin, GPIO_PULL_UP);
        gpio_set_pin_pull_mode(port->comm_pin1.pin, GPIO_PULL_UP);
        gpio_set_pin_function(port->comm_pin0.pin, port->comm_pin0.function); // SDA
        gpio_set_pin_function(port->comm_pin1.pin, port->comm_pin1.function); // SCL
        port->interfaceType = SensorPortComm_I2C;

        if (sercom_i2c_master_enable(&port->sercom.i2cm.sercom_instance) != I2CResult_Ok)
        {
            SensorPort_I2C_Disable(port);
            return SensorPort_I2C_Error;
        }

        return SensorPort_I2C_Success;
    }
    else
    {
        return SensorPort_I2C_Error;
    }
}

SensorPort_I2C_Status_t SensorPort_I2C_Disable(SensorPort_t* port)
{
   // ASSERT(port->interfaceType == SensorPortComm_I2C);

    gpio_set_pin_pull_mode(port->comm_pin0.pin, GPIO_PULL_OFF);
    gpio_set_pin_pull_mode(port->comm_pin1.pin, GPIO_PULL_OFF);

    gpio_set_pin_function(port->comm_pin0.pin, GPIO_PIN_FUNCTION_OFF);
    gpio_set_pin_function(port->comm_pin1.pin, GPIO_PIN_FUNCTION_OFF);

    sercom_i2c_master_deinit(&port->sercom.i2cm.sercom_instance);

    port->interfaceType = SensorPortComm_None;
    return SensorPort_I2C_Success;
}

SensorPort_I2C_Status_t SensorPort_I2C_StartWrite(SensorPort_t* port, uint16_t address, uint8_t* pData, size_t dataLength, I2CTransactionCallback_t callback)
{
    ASSERT(port->interfaceType == SensorPortComm_I2C);

    I2CTransaction_t transaction = {
        .slave_addr = address,
        .buffer = pData,
        .count = dataLength,
        .callback = callback,
        .type = I2CTransaction_Write
    };

    if (sercom_i2c_master_transfer(&port->sercom.i2cm.sercom_instance, &transaction) == I2CResult_Ok)
    {
        return SensorPort_I2C_Success;
    }
    else
    {
        return SensorPort_I2C_Error;
    }
}

SensorPort_I2C_Status_t SensorPort_I2C_StartRead(SensorPort_t* port, uint16_t address, uint8_t* pData, size_t dataLength, I2CTransactionCallback_t callback)
{
    ASSERT(port->interfaceType == SensorPortComm_I2C);

    I2CTransaction_t transaction = {
        .slave_addr = address,
        .buffer = pData,
        .count = dataLength,
        .callback = callback,
        .type = I2CTransaction_Read
    };

    if (sercom_i2c_master_transfer(&port->sercom.i2cm.sercom_instance, &transaction) == I2CResult_Ok)
    {
        return SensorPort_I2C_Success;
    }
    else
    {
        return SensorPort_I2C_Error;
    }
}

SensorPort_I2C_Status_t SensorPort_I2C_StartWriteFromISR(struct _SensorPort_t* port, uint16_t address, uint8_t* pData, size_t dataLength, I2CTransactionCallback_t callback)
{
    ASSERT(port->interfaceType == SensorPortComm_I2C);

    port->sercom.i2cm.sercom_instance.current_transaction.slave_addr = address;
    if (sercom_i2c_master_continue_write(&port->sercom.i2cm.sercom_instance, pData, dataLength, callback, false) == I2CResult_Ok)
    {
        return SensorPort_I2C_Success;
    }
    else
    {
        return SensorPort_I2C_Error;
    }
}

SensorPort_I2C_Status_t SensorPort_I2C_StartReadFromISR(struct _SensorPort_t* port, uint16_t address, uint8_t* pData, size_t dataLength, I2CTransactionCallback_t callback)
{
    ASSERT(port->interfaceType == SensorPortComm_I2C);

    port->sercom.i2cm.sercom_instance.current_transaction.slave_addr = address;
    if (sercom_i2c_master_continue_read(&port->sercom.i2cm.sercom_instance, pData, dataLength, callback, false) == I2CResult_Ok)
    {
        return SensorPort_I2C_Success;
    }
    else
    {
        return SensorPort_I2C_Error;
    }
}

SensorPort_I2C_Status_t SensorPort_I2C_ContinueWriteFromISR(struct _SensorPort_t* port, uint16_t address, uint8_t* pData, size_t dataLength, I2CTransactionCallback_t callback)
{
    ASSERT(port->interfaceType == SensorPortComm_I2C);

    port->sercom.i2cm.sercom_instance.current_transaction.slave_addr = address;
    if (sercom_i2c_master_continue_write(&port->sercom.i2cm.sercom_instance, pData, dataLength, callback, true) == I2CResult_Ok)
    {
        return SensorPort_I2C_Success;
    }
    else
    {
        return SensorPort_I2C_Error;
    }
}

SensorPort_I2C_Status_t SensorPort_I2C_ContinueReadFromISR(struct _SensorPort_t* port, uint16_t address, uint8_t* pData, size_t dataLength, I2CTransactionCallback_t callback)
{
    ASSERT(port->interfaceType == SensorPortComm_I2C);

    port->sercom.i2cm.sercom_instance.current_transaction.slave_addr = address;
    if (sercom_i2c_master_continue_read(&port->sercom.i2cm.sercom_instance, pData, dataLength, callback, true) == I2CResult_Ok)
    {
        return SensorPort_I2C_Success;
    }
    else
    {
        return SensorPort_I2C_Error;
    }
}

static void i2c_start_send_data(I2CMasterInstance_t* sercom_instance, size_t transferred)
{
    if (transferred == 1u)
    {
        SensorPort_I2CMaster_Instance_t* instance = CONTAINER_OF(sercom_instance, SensorPort_I2CMaster_Instance_t, sercom_instance);
        sercom_i2c_master_continue_write(&instance->sercom_instance, instance->dataBuffer, instance->bufferSize, instance->finishedCallback, true);
    }
}

static void i2c_start_read_data(I2CMasterInstance_t* sercom_instance, size_t transferred)
{
    if (transferred == 1u)
    {
        SensorPort_I2CMaster_Instance_t* instance = CONTAINER_OF(sercom_instance, SensorPort_I2CMaster_Instance_t, sercom_instance);
        sercom_i2c_master_continue_read(&instance->sercom_instance, instance->dataBuffer, instance->bufferSize, instance->finishedCallback, true);
    }
}

static SensorPort_I2C_Status_t i2c_send_reg_addr(SensorPort_t* port, uint16_t address, uint8_t reg, I2CTransactionCallback_t callback)
{
    port->sercom.i2cm.regAddress = reg;

    I2CTransaction_t transaction = {
        .slave_addr = address,
        .buffer = &port->sercom.i2cm.regAddress,
        .count = 1u,
        .callback = callback,
        .type = I2CTransaction_Write
    };

    if (sercom_i2c_master_transfer(&port->sercom.i2cm.sercom_instance, &transaction) == I2CResult_Ok)
    {
        return SensorPort_I2C_Success;
    }
    else
    {
        return SensorPort_I2C_Error;
    }
}

SensorPort_I2C_Status_t SensorPort_I2C_StartRegWrite(SensorPort_t* port, uint16_t address, uint8_t reg, uint8_t* pData, size_t dataLength, I2CTransactionCallback_t callback)
{
    ASSERT(port->interfaceType == SensorPortComm_I2C);

    port->sercom.i2cm.dataBuffer = pData;
    port->sercom.i2cm.bufferSize = dataLength;
    port->sercom.i2cm.finishedCallback = callback;

    return i2c_send_reg_addr(port, address, reg, &i2c_start_send_data);
}

SensorPort_I2C_Status_t SensorPort_I2C_StartRegRead(SensorPort_t* port, uint16_t address, uint8_t reg, uint8_t* pData, size_t dataLength, I2CTransactionCallback_t callback)
{
    ASSERT(port->interfaceType == SensorPortComm_I2C);

    port->sercom.i2cm.dataBuffer = pData;
    port->sercom.i2cm.bufferSize = dataLength;
    port->sercom.i2cm.finishedCallback = callback;

    return i2c_send_reg_addr(port, address, reg, &i2c_start_read_data);
}

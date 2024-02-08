#ifndef SENSOR_PORT_I2C_H_
#define SENSOR_PORT_I2C_H_

#include "libraries/sercom/sercom_i2c_master.h"

typedef struct {
    I2CMasterInstance_t sercom_instance;
    /* storage for callback continuation */
    uint8_t* dataBuffer;
    size_t bufferSize;
    I2CTransactionCallback_t finishedCallback;
    uint8_t regAddress;
} SensorPort_I2CMaster_Instance_t;

#include "../SensorPortHandlerInternal.h"

typedef enum {
    SensorPort_I2C_Success,
    SensorPort_I2C_Error
} SensorPort_I2C_Status_t;

SensorPort_I2C_Status_t SensorPort_I2C_Enable(struct _SensorPort_t* port, uint32_t baudrate);
SensorPort_I2C_Status_t SensorPort_I2C_Disable(struct _SensorPort_t* port);
SensorPort_I2C_Status_t SensorPort_I2C_StartWrite(struct _SensorPort_t* port, uint16_t address, uint8_t* pData, size_t dataLength, I2CTransactionCallback_t callback);
SensorPort_I2C_Status_t SensorPort_I2C_StartRead(struct _SensorPort_t* port, uint16_t address, uint8_t* pData, size_t dataLength, I2CTransactionCallback_t callback);
SensorPort_I2C_Status_t SensorPort_I2C_StartWriteFromISR(struct _SensorPort_t* port, uint16_t address, uint8_t* pData, size_t dataLength, I2CTransactionCallback_t callback);
SensorPort_I2C_Status_t SensorPort_I2C_StartReadFromISR(struct _SensorPort_t* port, uint16_t address, uint8_t* pData, size_t dataLength, I2CTransactionCallback_t callback);
SensorPort_I2C_Status_t SensorPort_I2C_ContinueWriteFromISR(struct _SensorPort_t* port, uint16_t address, uint8_t* pData, size_t dataLength, I2CTransactionCallback_t callback);
SensorPort_I2C_Status_t SensorPort_I2C_ContinueReadFromISR(struct _SensorPort_t* port, uint16_t address, uint8_t* pData, size_t dataLength, I2CTransactionCallback_t callback);
SensorPort_I2C_Status_t SensorPort_I2C_StartRegWrite(struct _SensorPort_t* port, uint16_t address, uint8_t reg, uint8_t* pData, size_t dataLength, I2CTransactionCallback_t callback);
SensorPort_I2C_Status_t SensorPort_I2C_StartRegRead(struct _SensorPort_t* port, uint16_t address, uint8_t reg, uint8_t* pData, size_t dataLength, I2CTransactionCallback_t callback);

#endif /* SENSOR_PORT_I2C_H_ */

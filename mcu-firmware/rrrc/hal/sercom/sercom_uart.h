#ifndef SERCOM_UART_H_
#define SERCOM_UART_H_

#include "sercom_base.h"
#include <stdint.h>

typedef enum {
    UARTResult_Ok,
    UARTResult_Busy,
    UARTResult_Error
} UARTResult_t;

typedef struct {
    void* hw;
    uint32_t baud_rate;
} UARTConfig_t;

struct __UARTInstance_t;

typedef void (*UARTByteReceivedCallback_t)(struct __UARTInstance_t* instance, uint8_t data);
typedef void (*UARTTxCompleteCallback_t)(struct __UARTInstance_t* instance);

typedef struct __UARTInstance_t {
    void* hw;
    UARTByteReceivedCallback_t rxCallback;
    UARTTxCompleteCallback_t txComplete;
    const uint8_t* txBuffer;
    size_t txCount;
} UARTInstance_t;

UARTResult_t sercom_uart_init(UARTInstance_t* instance, const UARTConfig_t* config);
UARTResult_t sercom_uart_deinit(UARTInstance_t* instance);

UARTResult_t sercom_uart_write(UARTInstance_t* instance, const uint8_t* buffer, size_t count, UARTTxCompleteCallback_t callback);
UARTResult_t sercom_uart_start_reception(UARTInstance_t* instance, UARTByteReceivedCallback_t callback);
UARTResult_t sercom_uart_stop_reception(UARTInstance_t* instance);

#endif /* SERCOM_UART_H_ */

#include "sercom_uart.h"
#include <math.h>

/* Asynchronous UART implementation to support reconfigurable interfaces.
 * this implementation assumes 24MHz clock and 
 * a lot of settings that are fixed in our application
 */

#define UART_INT_HANDLER_DR_EMPTY              0
#define UART_INT_HANDLER_TX_COMPLETE           1
#define UART_INT_HANDLER_RX_COMPLETE           2
#define UART_INT_HANDLER_RX_START              3
#define UART_INT_HANDLER_CLEAR_TO_SEND_CHANGE  3
#define UART_INT_HANDLER_RECEIVE_BREAK         3
#define UART_INT_HANDLER_ERROR                 3

/* TODO: explore 32bit extension for data transmission */
static void uart_send_buffer(UARTInstance_t* instance)
{
    if (instance->txCount == 0u)
    {
        instance->txBuffer = NULL;
        hri_sercomusart_clear_INTFLAG_TXC_bit(instance->hw);
        if (instance->txComplete)
        {
            instance->txComplete(instance);
        }
    }
    else
    {
        uint32_t data = (uint32_t) *instance->txBuffer;

        hri_sercomusart_write_DATA_reg(instance->hw, data);

        --instance->txCount;
        ++instance->txBuffer;
    }
}

static void uart_tx_callback(void* data)
{
    UARTInstance_t* instance = (UARTInstance_t*) data;

    uart_send_buffer(instance);
}

static void uart_rx_callback(void* data)
{
    UARTInstance_t* instance = (UARTInstance_t*) data;

    uint8_t rxData = (uint8_t) hri_sercomusart_read_DATA_reg(instance->hw);

    /* there is always a callback if rx interrupt is enabled */
    instance->rxCallback(instance, rxData);
}

UARTResult_t sercom_uart_init(UARTInstance_t* instance, const UARTConfig_t* config)
{
    if (instance->hw != NULL)
    {
        return UARTResult_Busy;
    }

    if (sercom_init(config->hw, instance) == SercomResult_Ok)
    {
        instance->hw = config->hw;
     
        hri_sercomusart_set_CTRLA_SWRST_bit(instance->hw);
        
        /* CTRLA:
         * - LSB first
         * - asynchronous
         * - no parity
         * - 7-8-9 samples
         * - RX on PAD1
         * - TX on PAD0
         * - 16x sample rate
         * - not inverted rx/tx
         * - wake up in standby
         * - internal clock */
        
        uint32_t ctrl_a = SERCOM_USART_CTRLA_DORD
                        | SERCOM_USART_CTRLA_MODE(0x01) 
                        | SERCOM_USART_CTRLA_FORM(0)
                        | SERCOM_USART_CTRLA_SAMPA(0)
                        | SERCOM_USART_CTRLA_TXPO(2)
                        | SERCOM_USART_CTRLA_RXPO(1)
                        | SERCOM_USART_CTRLA_SAMPR(0)
                        | SERCOM_USART_CTRLA_RUNSTDBY;

        /* CTRLB:
         * normal USART
         * RXEN, TXEN = 1
         * not encoded
         * no start of frame detection
         * no collision detection
         * CHSIZE = 8 bit
         * 1 stop bit
         */
        uint32_t ctrl_b = SERCOM_USART_CTRLB_RXEN | SERCOM_USART_CTRLB_TXEN;

        /* CTRLC:
         * no 32bit extension, TODO
         * other bits irrelevant
         */
        uint32_t ctrl_c = 0u;
        
        hri_sercomusart_write_CTRLA_reg(instance->hw, ctrl_a);
        hri_sercomusart_write_CTRLB_reg(instance->hw, ctrl_b);
        hri_sercomusart_write_CTRLC_reg(instance->hw, ctrl_c);
        
        uint16_t baud = (uint16_t)lroundf(65536.0f - (65536.0f * 16.0f * config->baud_rate) / 24000000.0f);
        hri_sercomusart_write_BAUD_reg(instance->hw, baud);

        hri_sercomusart_write_RXPL_reg(instance->hw, 0u); // only relevant in IrDA mode
        hri_sercomusart_write_DBGCTRL_reg(instance->hw, 0u);

        hri_sercomusart_write_INTEN_RXC_bit(instance->hw, true);
        hri_sercomusart_write_INTEN_TXC_bit(instance->hw, true);

        hri_sercomusart_set_CTRLA_ENABLE_bit(instance->hw);

        return UARTResult_Ok;
    }
    else
    {
        return UARTResult_Error;
    }
}

UARTResult_t sercom_uart_deinit(UARTInstance_t* instance)
{
    if (sercom_deinit(instance) == SercomResult_Ok)
    {
        hri_sercomusart_set_CTRLA_SWRST_bit(instance->hw);
        instance->hw = NULL;

        return UARTResult_Ok;
    }
    else
    {
        return UARTResult_Error;
    }
}

UARTResult_t sercom_uart_write(UARTInstance_t* instance, const uint8_t* buffer, size_t count, UARTTxCompleteCallback_t callback)
{
    if (instance->txBuffer != NULL)
    {
        return UARTResult_Busy;
    }
   
    
    if (buffer == NULL)
    {
        return UARTResult_Error;
    }

    if (count == 0u)
    {
        if (callback)
        {
            callback(instance);
        }
    }
    else
    {
        instance->txCount = count;
        instance->txBuffer = buffer;
        instance->txComplete = callback;

        // "Writing these bits will write the Transmit Data register. This register should be written only
        // when the Data Register Empty Interrupt Flag bit in the Interrupt Flag Status
        // and Clear register (INTFLAG.DRE) is set."
        sercom_set_interrupt_handler(instance, UART_INT_HANDLER_TX_COMPLETE, &uart_tx_callback);

        uart_send_buffer(instance);
    }

    return UARTResult_Ok;
}

UARTResult_t sercom_uart_start_reception(UARTInstance_t* instance, UARTByteReceivedCallback_t callback)
{
    if (instance->rxCallback != NULL)
    {
        return UARTResult_Busy;
    }
    else
    {
        instance->rxCallback = callback;

        if (callback == NULL)
        {
            return UARTResult_Error;
        }

        /* receiver is always running, no need to start, ignore last data */
        (void) hri_sercomusart_read_DATA_reg(instance->hw);
        sercom_set_interrupt_handler(instance, UART_INT_HANDLER_RX_COMPLETE, &uart_rx_callback);

        return UARTResult_Ok;
    }
}

UARTResult_t sercom_uart_stop_reception(UARTInstance_t* instance)
{
    if (instance->rxCallback != NULL)
    {
        /* receiver is always running, no need to stop */
        sercom_set_interrupt_handler(instance, UART_INT_HANDLER_RX_COMPLETE, NULL);
        instance->rxCallback = NULL;
    }
    
    return UARTResult_Ok;
}

#include "MasterCommunicationInterface.h"

#include "i2cHal.h"

#include "SEGGER_RTT.h"
#include "driver_init.h"
#include "utils_assert.h"
#include <peripheral_clk_config.h>
#include <limits.h>

#define RX_BUFFER_OVERFLOW ((ssize_t) -1)

static ssize_t messageSize;
static bool messageReceived;
static const uint8_t* messageBuffer;

static bool tx_complete = false;

const MasterCommunicationInterface_Config_t* config;

//*********************************************************************************************
static int32_t I2C_4_init(uint8_t address)
{
    hri_gclk_write_PCHCTRL_reg(GCLK, SERCOM2_GCLK_ID_CORE, CONF_GCLK_SERCOM2_CORE_SRC | (1 << GCLK_PCHCTRL_CHEN_Pos));
    hri_gclk_write_PCHCTRL_reg(GCLK, SERCOM2_GCLK_ID_SLOW, CONF_GCLK_SERCOM2_SLOW_SRC | (1 << GCLK_PCHCTRL_CHEN_Pos));
    hri_mclk_set_APBBMASK_SERCOM2_bit(MCLK);

    gpio_set_pin_pull_mode(I2C4_SDApin, GPIO_PULL_OFF);
    gpio_set_pin_function(I2C4_SDApin, I2C4_SDApin_function);
    gpio_set_pin_pull_mode(I2C4_SCLpin, GPIO_PULL_OFF);
    gpio_set_pin_function(I2C4_SCLpin, I2C4_SCLpin_function);

    return i2c_hal_init(I2C4_SERCOM, address);
}

void i2c_hal_rx_started(void)
{
    MasterCommunicationInterface_Run_SetResponse(config->default_response);
}

void i2c_hal_rx_complete(const uint8_t* buffer, size_t bufferSize, size_t bytesReceived)
{
    if (bufferSize < bytesReceived) {
        messageSize = RX_BUFFER_OVERFLOW;
    } else {
        messageSize = (ssize_t)bytesReceived;
    }
    messageReceived = true;
    messageBuffer = buffer;
}

void i2c_hal_tx_complete(void)
{
    tx_complete = true;
}

void sercom2_rx_done_cb(uint8_t data)
{
    i2c_hal_on_rx_done(data);
}

void MasterCommunicationInterface_Run_OnInit(const MasterCommunicationInterface_Config_t* cfg)
{
    messageReceived = false;
    config = cfg;

    (void) I2C_4_init(0x2B);
    i2c_hal_receive();
}

void MasterCommunicationInterface_Run_Update(void)
{
    if (messageReceived)
    {
        messageReceived = false;
        if (messageSize > 0)
        {
            ConstByteArray_t message = {.bytes = messageBuffer, .count = messageSize};
            MasterCommunicationInterface_RaiseEvent_OnMessageReceived(message);
        }
        else
        {
            MasterCommunicationInterface_Run_SetResponse(config->rx_overflow_response);
        }
    }

    if (tx_complete)
    {
        tx_complete = false;
        MasterCommunicationInterface_Call_OnTransmitComplete();
    }
}

__attribute__((weak))
void MasterCommunicationInterface_RaiseEvent_OnMessageReceived(ConstByteArray_t message)
{
    /* nothing to do */
    (void) message;
}

__attribute__((weak))
void MasterCommunicationInterface_Call_OnTransmitComplete(void)
{
    /* nothing to do */
}

void MasterCommunicationInterface_Run_SetResponse(ConstByteArray_t response)
{
    i2c_hal_receive();
    i2c_hal_set_tx_buffer(response.bytes, response.count);
}

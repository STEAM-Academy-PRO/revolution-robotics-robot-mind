#include "MasterCommunicationInterface_Bootloader.h"
#include "utils.h"
#include "utils_assert.h"

/* Begin User Code Section: Declarations */
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

static MasterCommunicationInterface_Config_t config;

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
    MasterCommunicationInterface_Bootloader_Run_SetResponse(config.default_response);
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
/* End User Code Section: Declarations */

void MasterCommunicationInterface_Bootloader_Run_OnInit(void)
{
    /* Begin User Code Section: OnInit:run Start */
    MasterCommunicationInterface_Bootloader_Read_Configuration(&config);

    messageReceived = false;

    (void) I2C_4_init(0x2Bu); // TODO: move constant to project configuration
    i2c_hal_receive();
    /* End User Code Section: OnInit:run Start */
    /* Begin User Code Section: OnInit:run End */

    /* End User Code Section: OnInit:run End */
}

void MasterCommunicationInterface_Bootloader_Run_Update(void)
{
    /* Begin User Code Section: Update:run Start */
    if (messageReceived)
    {
        messageReceived = false;
        if (messageSize > 0)
        {
            ConstByteArray_t message = {.bytes = messageBuffer, .count = messageSize};
            MasterCommunicationInterface_Bootloader_RaiseEvent_OnMessageReceived(message);
        }
        else
        {
            MasterCommunicationInterface_Bootloader_Run_SetResponse(config.rx_overflow_response);
        }
    }

    if (tx_complete)
    {
        tx_complete = false;
        MasterCommunicationInterface_Bootloader_RaiseEvent_OnTransmissionComplete();
    }
    /* End User Code Section: Update:run Start */
    /* Begin User Code Section: Update:run End */

    /* End User Code Section: Update:run End */
}

void MasterCommunicationInterface_Bootloader_Run_SetResponse(ConstByteArray_t response)
{
    /* Begin User Code Section: SetResponse:run Start */
    i2c_hal_receive();
    i2c_hal_set_tx_buffer(response.bytes, response.count);
    /* End User Code Section: SetResponse:run Start */
    /* Begin User Code Section: SetResponse:run End */

    /* End User Code Section: SetResponse:run End */
}

__attribute__((weak))
void MasterCommunicationInterface_Bootloader_RaiseEvent_RxTimeout(void)
{
    /* Begin User Code Section: RxTimeout:run Start */

    /* End User Code Section: RxTimeout:run Start */
    /* Begin User Code Section: RxTimeout:run End */

    /* End User Code Section: RxTimeout:run End */
}

__attribute__((weak))
void MasterCommunicationInterface_Bootloader_RaiseEvent_OnMessageReceived(ConstByteArray_t message)
{
    (void) message;
    /* Begin User Code Section: OnMessageReceived:run Start */

    /* End User Code Section: OnMessageReceived:run Start */
    /* Begin User Code Section: OnMessageReceived:run End */

    /* End User Code Section: OnMessageReceived:run End */
}

__attribute__((weak))
void MasterCommunicationInterface_Bootloader_RaiseEvent_OnTransmissionComplete(void)
{
    /* Begin User Code Section: OnTransmissionComplete:run Start */

    /* End User Code Section: OnTransmissionComplete:run Start */
    /* Begin User Code Section: OnTransmissionComplete:run End */

    /* End User Code Section: OnTransmissionComplete:run End */
}

__attribute__((weak))
void MasterCommunicationInterface_Bootloader_Read_Configuration(MasterCommunicationInterface_Config_t* value)
{
    ASSERT(value != NULL);
    /* Begin User Code Section: Configuration:read Start */

    /* End User Code Section: Configuration:read Start */
    *value = (MasterCommunicationInterface_Config_t) {
        .default_response     = {
            .bytes = NULL,
            .count = 0u
        },
        .rx_overflow_response = {
            .bytes = NULL,
            .count = 0u
        },
        .rx_timeout           = 0u
    };
    /* Begin User Code Section: Configuration:read End */

    /* End User Code Section: Configuration:read End */
}

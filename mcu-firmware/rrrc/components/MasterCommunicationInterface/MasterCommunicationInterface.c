#include "MasterCommunicationInterface.h"
#include "utils.h"
#include "utils_assert.h"

/* Begin User Code Section: Declarations */
#include "i2cHal.h"
#include "rrrc_hal.h"

#include "driver_init.h"
#include "FreeRTOS.h"
#include "task.h"
#include <peripheral_clk_config.h>
#include <limits.h>
#include "error_ids.h"
#include "SEGGER_RTT.h"

static TaskHandle_t communicationTaskHandle;

static MasterCommunicationInterface_Config_t config;

const uint32_t RX_DONE = 0x80000000u;
const uint32_t RX_BUFFER_OVERFLOW = 0x40000000u;
const uint32_t TX_DONE = 0x20000000u; /** < Pi read data from MCU buffer */

static const uint8_t* rxBuffer;

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

static void CommunicationTask(void *user_data)
{
    (void)user_data;

    i2c_hal_receive();
    for (;;)
    {
        uint32_t rxFlags;
        BaseType_t notified = xTaskNotifyWait(0, ULONG_MAX, &rxFlags, config.rx_timeout);

        if (!notified)
        {
            MasterCommunicationInterface_RaiseEvent_RxTimeout();
        }
        else
        {
            if ((rxFlags & RX_DONE) != 0)
            {
                uint32_t bytesReceived = rxFlags & ~(TX_DONE | RX_BUFFER_OVERFLOW | RX_DONE);
                if ((rxFlags & RX_BUFFER_OVERFLOW) != 0)
                {
                    SEGGER_RTT_printf(0, "Rx overflow: %d received\n", bytesReceived);
                    MasterCommunicationInterface_Run_SetResponse(config.rx_overflow_response);
                }
                else
                {
                    ConstByteArray_t message = {.bytes = rxBuffer, .count = bytesReceived};
                    MasterCommunicationInterface_RaiseEvent_OnMessageReceived(message);
                }
            }

            if ((rxFlags & TX_DONE) != 0)
            {
                MasterCommunicationInterface_RaiseEvent_OnTransmissionComplete();
            }
        }
    }
}

void i2c_hal_rx_started(void)
{
    /* setup a default response in case processing is slow */
    MasterCommunicationInterface_Run_SetResponse(config.default_response);
}

void i2c_hal_rx_complete(const uint8_t *buffer, size_t bufferSize, size_t bytesReceived)
{
    rxBuffer = buffer;

    ASSERT(communicationTaskHandle);

    BaseType_t xHigherPriorityTaskWoken = pdFALSE;
    if (bufferSize < bytesReceived) {
        xTaskNotifyFromISR(communicationTaskHandle, RX_DONE | RX_BUFFER_OVERFLOW, eSetBits, &xHigherPriorityTaskWoken);
    } else {
        xTaskNotifyFromISR(communicationTaskHandle, RX_DONE | bytesReceived, eSetBits, &xHigherPriorityTaskWoken);
    }
    portYIELD_FROM_ISR(xHigherPriorityTaskWoken);
}

void i2c_hal_tx_complete(void)
{
    ASSERT(communicationTaskHandle);

    BaseType_t xHigherPriorityTaskWoken = pdFALSE;
    xTaskNotifyFromISR(communicationTaskHandle, TX_DONE, eSetBits, &xHigherPriorityTaskWoken);
    portYIELD_FROM_ISR(xHigherPriorityTaskWoken);
}
/* End User Code Section: Declarations */

void MasterCommunicationInterface_Run_OnInit(void)
{
    /* Begin User Code Section: OnInit:run Start */
    MasterCommunicationInterface_Read_Configuration(&config);

    int32_t result = I2C_4_init(MasterCommunicationInterface_Read_DeviceAddress());
    ASSERT(result == ERR_NONE);

    BaseType_t success = xTaskCreate(&CommunicationTask, "RPiComm", 1024u, NULL, taskPriority_Communication, &communicationTaskHandle);
    ASSERT(success == pdPASS);
    /* End User Code Section: OnInit:run Start */
    /* Begin User Code Section: OnInit:run End */

    /* End User Code Section: OnInit:run End */
}

void MasterCommunicationInterface_Run_SetResponse(ConstByteArray_t response)
{
    /* Begin User Code Section: SetResponse:run Start */
    i2c_hal_receive();
    i2c_hal_set_tx_buffer(response.bytes, response.count);
    /* End User Code Section: SetResponse:run Start */
    /* Begin User Code Section: SetResponse:run End */

    /* End User Code Section: SetResponse:run End */
}

__attribute__((weak))
void MasterCommunicationInterface_RaiseEvent_RxTimeout(void)
{
    /* Begin User Code Section: RxTimeout:run Start */

    /* End User Code Section: RxTimeout:run Start */
    /* Begin User Code Section: RxTimeout:run End */

    /* End User Code Section: RxTimeout:run End */
}

__attribute__((weak))
void MasterCommunicationInterface_RaiseEvent_OnMessageReceived(ConstByteArray_t message)
{
    (void) message;
    /* Begin User Code Section: OnMessageReceived:run Start */

    /* End User Code Section: OnMessageReceived:run Start */
    /* Begin User Code Section: OnMessageReceived:run End */

    /* End User Code Section: OnMessageReceived:run End */
}

__attribute__((weak))
void MasterCommunicationInterface_RaiseEvent_OnTransmissionComplete(void)
{
    /* Begin User Code Section: OnTransmissionComplete:run Start */

    /* End User Code Section: OnTransmissionComplete:run Start */
    /* Begin User Code Section: OnTransmissionComplete:run End */

    /* End User Code Section: OnTransmissionComplete:run End */
}

__attribute__((weak))
void MasterCommunicationInterface_Call_LogError(const ErrorInfo_t* data)
{
    (void) data;
    /* Begin User Code Section: LogError:run Start */

    /* End User Code Section: LogError:run Start */
    /* Begin User Code Section: LogError:run End */

    /* End User Code Section: LogError:run End */
}

__attribute__((weak))
void MasterCommunicationInterface_Read_Configuration(MasterCommunicationInterface_Config_t* value)
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

__attribute__((weak))
uint8_t MasterCommunicationInterface_Read_DeviceAddress(void)
{
    /* Begin User Code Section: DeviceAddress:read Start */

    /* End User Code Section: DeviceAddress:read Start */
    /* Begin User Code Section: DeviceAddress:read End */

    /* End User Code Section: DeviceAddress:read End */
    return 0;
}

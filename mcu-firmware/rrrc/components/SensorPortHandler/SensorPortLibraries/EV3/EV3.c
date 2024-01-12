#include "EV3.h"
#include <string.h>

#include "ev3_lib.h"

#define EV3_STATUS_IDLE      0x00
#define EV3_STATUS_CONFIGURE 0x40
#define EV3_STATUS_DATA      0x80

typedef struct {
    EV3Instance_t ev3;
    uint8_t txBuffer[3]; /* cmd + mode (select) + crc?? */
} EV3SensorDriverData_t;

static void ev3_indicate_state(SensorPort_t* sensorPort, uint8_t sensor_status)
{
    ByteArray_t status = {
        .bytes = &sensor_status,
        .count = 1u
    };
    SensorPortHandler_Call_UpdatePortStatus(sensorPort->port_idx, status);
}

static bool peek_rx_buffer(EV3SensorDriverData_t* instance, uint8_t* dst)
{
    if (instance->ev3.rxBufferCount > 0u)
    {
        *dst = instance->ev3.rxBuffer[instance->ev3.rxBufferRIdx];
        return true;
    }
    else
    {
        return false;
    }
}

static bool read_rx_buffer(EV3SensorDriverData_t* instance, uint8_t* data)
{
    bool read = false;
    __disable_irq();
    if (instance->ev3.rxBufferCount > 0u)
    {
        if (data != NULL)
        {
            *data = instance->ev3.rxBuffer[instance->ev3.rxBufferRIdx];
        }
        instance->ev3.rxBufferRIdx = (instance->ev3.rxBufferRIdx + 1u) % ARRAY_SIZE(instance->ev3.rxBuffer);
        --instance->ev3.rxBufferCount;
        read = true;
    }
    __enable_irq();

    return read;
}

static size_t rx_buffer_copy(EV3SensorDriverData_t* instance, uint8_t* dst, size_t count)
{
    size_t copied = 0;
    for (size_t i = 0u; i < count; i++)
    {
        if (read_rx_buffer(instance, &dst[i]))
        {
            copied += 1u;
        }
        else
        {
            break;
        }
    }

    return copied;
}

static void flush_rx_buffer(EV3SensorDriverData_t* instance)
{
    __disable_irq();
    instance->ev3.rxBufferCount = 0u;
    instance->ev3.rxBufferRIdx = 0u;
    __enable_irq();
}

static void write_rx_buffer(EV3SensorDriverData_t* instance, uint8_t data)
{
    __disable_irq();
    if (instance->ev3.rxBufferCount < ARRAY_SIZE(instance->ev3.rxBuffer))
    {
        uint8_t wptr = (instance->ev3.rxBufferRIdx + instance->ev3.rxBufferCount) % ARRAY_SIZE(instance->ev3.rxBuffer);
        instance->ev3.rxBuffer[wptr] = data;
        instance->ev3.rxBufferCount++;
    }
    __enable_irq();
}

static void uart_rx_complete(UARTInstance_t* instance, uint8_t data)
{
    EV3SensorDriverData_t* libdata = (EV3SensorDriverData_t*) CONTAINER_OF(instance, SensorPort_t, sercom.uart)->libraryData;

    write_rx_buffer(libdata, data);
}

static void uart_active_rx_complete(UARTInstance_t* instance, uint8_t data)
{
    SensorPort_t* sensorPort = CONTAINER_OF(instance, SensorPort_t, sercom.uart);
    EV3SensorDriverData_t* libdata = (EV3SensorDriverData_t*) sensorPort->libraryData;

    if (libdata->ev3.state != EV3State_Active)
    {
        return;
    }

    write_rx_buffer(libdata, data);

    uint8_t cmd;
    if (peek_rx_buffer(libdata, &cmd))
    {
        EV3Message_t message = ev3_get_message_type(cmd);
        uint8_t length = ev3_command_length(cmd);
        
        if (message == EV3Message_Data)
        {
            if (libdata->ev3.rxBufferCount >= length)
            {
                size_t copied = rx_buffer_copy(libdata, libdata->ev3.dataBuffer, length);
                if (ev3_check_crc(libdata->ev3.dataBuffer, copied) || ev3_provides_wrong_crc(&libdata->ev3, cmd))
                {
                    libdata->ev3.errorCount = 0u;
                    libdata->ev3.dataBuffer[0] = EV3_STATUS_DATA | (cmd & 0x07u);

                    SensorPortHandler_Call_UpdatePortStatus(sensorPort->port_idx, (ByteArray_t){
                        .bytes = &libdata->ev3.dataBuffer[0],
                        .count = libdata->ev3.modes[libdata->ev3.current_mode].rawSize + 1u
                    });
                }
                else
                {
                    ++libdata->ev3.errorCount;
                }
            }
        }
        else
        {
            (void) read_rx_buffer(libdata, NULL);
        }
    }
}

static void uart_ack_tx_complete(UARTInstance_t* instance)
{
    SensorPort_t* port = CONTAINER_OF(instance, SensorPort_t, sercom.uart);

    EV3SensorDriverData_t* libdata = (EV3SensorDriverData_t*) port->libraryData;

    /* reconfigure to new UART speed */
    SensorPort_UART_Disable(port);
    SensorPort_SetOrangeLed(port, false);
    SensorPort_UART_Enable(port, libdata->ev3.speed);
    flush_rx_buffer(libdata);
    SensorPort_UART_Receive(port, &uart_active_rx_complete);
}

static void ev3_send_nack(SensorPort_t* port, EV3SensorDriverData_t* libdata)
{
    libdata->txBuffer[0] = 0x02u;
    (void) SensorPort_UART_Transmit(port, libdata->txBuffer, 1u, NULL);
}

static void ev3_send_ack(SensorPort_t* port, EV3SensorDriverData_t* libdata)
{
    libdata->txBuffer[0] = 0x04u;
    SensorPort_UART_Receive(port, NULL);
    (void) SensorPort_UART_Transmit(port, libdata->txBuffer, 1u, &uart_ack_tx_complete);
}

static bool ev3_send_mode_switch(SensorPort_t* port, EV3SensorDriverData_t* libdata, uint8_t mode)
{
    /* FIXME a more general write function could be used here */
    libdata->txBuffer[0] = 0x43u;
    libdata->txBuffer[1] = mode;
    libdata->txBuffer[2] = 0xFFu ^ 0x43u ^ mode;
    return SensorPort_UART_Transmit(port, libdata->txBuffer, 3u, NULL) == SensorPort_UART_Success;
}

static void ev3_enter_state(SensorPort_t* sensorPort, EV3SensorDriverData_t* instance, EV3State_t state)
{
    switch (state)
    {
        case EV3State_Reset:
        {
            ev3_indicate_state(sensorPort, EV3_STATUS_IDLE);
            if (instance->ev3.state != EV3State_Reset)
            {
                SensorPort_UART_Disable(sensorPort);
            }
            instance->ev3.errorCount = 0u;
            instance->ev3.speed = 2400u;
            
            instance->ev3.nModes = 1u;
            instance->ev3.nViews = 1u;
            
            instance->ev3.current_mode = 0u;
            
            for (size_t i = 0u; i < ARRAY_SIZE(instance->ev3.modes); i++)
            {
                /* invalid data type to check if info was received */
                instance->ev3.modes[i].dataType = EV3Data_invalid;
            }
        }
            break;

        case EV3State_ReadType:
            ev3_indicate_state(sensorPort, EV3_STATUS_CONFIGURE);
            break;

        case EV3State_Initialize:
            instance->ev3.nModes = 1u;
            instance->ev3.nViews = 1u;
            instance->ev3.current_mode = 0u;
            break;

        case EV3State_Active:
            if (instance->ev3.nModes != ev3_count_initialized_modes(&instance->ev3))
            {
                /* we don't have all the required info to start */
                ev3_enter_state(sensorPort, instance, EV3State_Reset);
                return;
            }
            ev3_send_ack(sensorPort, instance);
            instance->ev3.heartbeat_counter = 0u;
            break;

        default:
            ASSERT(0);
            break;
    }
    instance->ev3.state = state;
}

void ev3_run_reset(SensorPort_t* sensorPort, EV3SensorDriverData_t* libdata)
{
    SensorPort_SetOrangeLed(sensorPort, true);

    SensorPort_UART_Enable(sensorPort, 2400u);

    SensorPort_UART_Receive(sensorPort, &uart_rx_complete);

    flush_rx_buffer(libdata);
    ev3_enter_state(sensorPort, libdata, EV3State_ReadType);
}

void ev3_update_read_type(SensorPort_t* sensorPort, EV3SensorDriverData_t* libdata)
{
    /* Ignore all messages except TYPE until we get a valid TYPE message
     * This can be done here because the cycle time is 20ms and at 2400 baud/s (1920bit/s)
     *   we get about 40 bytes per cycle
     */
    uint8_t cmd;
    bool found_start = false;
    while (peek_rx_buffer(libdata, &cmd))
    {
        if (cmd == 0x40u)
        {
            found_start = true;
            break;
        }
        else
        {
            (void) read_rx_buffer(libdata, NULL); /* throw away byte */
        }
    }

    if (found_start && libdata->ev3.rxBufferCount >= 3u)
    {
        bool success = read_rx_buffer(libdata, &cmd);

        uint8_t sensor_type = 0u;
        uint8_t expected_crc = 0u;

        success &= read_rx_buffer(libdata, &sensor_type);
        success &= read_rx_buffer(libdata, &expected_crc);

        if (success)
        {
            uint8_t crc = 0xFFu ^ cmd ^ sensor_type;

            if (crc == expected_crc)
            {
                libdata->ev3.sensor_type = sensor_type;
                ev3_enter_state(sensorPort, libdata, EV3State_Initialize);
            }
        }
    }
}

void ev3_update_initialize(SensorPort_t* sensorPort, EV3SensorDriverData_t* libdata)
{
    /* in this state we assume to be in sync with the sensor */
    /* read INFO messages, move to Active state if an ACK is received */
    uint8_t cmd;
    if (peek_rx_buffer(libdata, &cmd))
    {
        EV3Message_t message = ev3_get_message_type(cmd);
        uint8_t length = ev3_command_length(cmd);

        if (message == EV3Message_Sync)
        {
            if (libdata->ev3.sensor_type == 33u)
            {
                 /* IR sensor sends CRC after SYNC
                  * (https://github.com/ev3dev/lego-linux-drivers/blob/ev3dev-buster/sensors/ev3_uart_sensor_ld.c#L653) */
                length = 2u;
            }
        }

        if (libdata->ev3.rxBufferCount < length) /* wait for a full message: cmd + length + crc */
        {
            return;
        }

        size_t copied = rx_buffer_copy(libdata, libdata->ev3.dataBuffer, length);

        if (!ev3_check_crc(libdata->ev3.dataBuffer, copied))
        {
            /* don't tolerate init messages with incorrect crc */
            ev3_enter_state(sensorPort, libdata, EV3State_Reset);
            return;
        }

        switch (message)
        {
            case EV3Message_Sync:
                break;

            case EV3Message_Type:
                /* this means we missed something during initialization and the sensor has reset */
                libdata->ev3.sensor_type = libdata->ev3.dataBuffer[1];
                ev3_enter_state(sensorPort, libdata, EV3State_Initialize);
                break;
                
            case EV3Message_Ack:
                ev3_enter_state(sensorPort, libdata, EV3State_Active);
                break;

            case EV3Message_Speed:
                if (copied == 6u)
                {
                    memcpy(&libdata->ev3.speed, &libdata->ev3.dataBuffer[1], 4u);
                }
                else
                {
                    ev3_enter_state(sensorPort, libdata, EV3State_Reset);
                }
                break;

            case EV3Message_Modes:
                libdata->ev3.nModes = libdata->ev3.dataBuffer[1] + 1u;
                if (copied > 3)
                {
                    libdata->ev3.nViews = libdata->ev3.dataBuffer[2] + 1u;
                }
                break;

            case EV3Message_Info: {
                uint8_t mode = cmd & 0x07u;

                if (mode > libdata->ev3.nModes)
                {
                    ev3_enter_state(sensorPort, libdata, EV3State_Reset);
                    return;
                }

                switch (libdata->ev3.dataBuffer[1])
                {
                    case INFO_UNITS:
                        break;

                    case INFO_NAME:
                        break;

                    case INFO_RAW:
                        memcpy(&libdata->ev3.modes[mode].raw_min, &libdata->ev3.dataBuffer[2], 4u);
                        memcpy(&libdata->ev3.modes[mode].raw_max, &libdata->ev3.dataBuffer[6], 4u);
                        break;

                    case INFO_PCT:
                        memcpy(&libdata->ev3.modes[mode].pct_min, &libdata->ev3.dataBuffer[2], 4u);
                        memcpy(&libdata->ev3.modes[mode].pct_max, &libdata->ev3.dataBuffer[6], 4u);
                        break;
                        
                    case INFO_SI:
                        memcpy(&libdata->ev3.modes[mode].si_min, &libdata->ev3.dataBuffer[2], 4u);
                        memcpy(&libdata->ev3.modes[mode].si_max, &libdata->ev3.dataBuffer[6], 4u);
                        break;

                    case INFO_FORMAT:
                        if (copied == 7u)
                        {
                            if (!ev3_process_mode_format(&libdata->ev3.modes[mode], libdata->ev3.dataBuffer))
                            {
                                ev3_enter_state(sensorPort, libdata, EV3State_Reset);
                            }
                        }
                        else
                        {
                            ev3_enter_state(sensorPort, libdata, EV3State_Reset);
                        }
                        break;

                    default:
                        /* invalid */
                        ev3_enter_state(sensorPort, libdata, EV3State_Reset);
                        break;
                }
            }
                break;

            default:
                /* unexpected command */
                ev3_enter_state(sensorPort, libdata, EV3State_Reset);
                break;
        }
    }
}

void ev3_update_active(SensorPort_t* sensorPort, EV3SensorDriverData_t* libdata)
{
    if (libdata->ev3.errorCount > ERROR_THRESHOLD)
    {
        ev3_enter_state(sensorPort, libdata, EV3State_Reset);
    }
    else if (libdata->ev3.heartbeat_counter == HEARTBEAT_LIMIT)
    {
        libdata->ev3.heartbeat_counter = 0u;
        ev3_send_nack(sensorPort, libdata);

        /* receiving a valid message zeros this counter */
        __disable_irq();
        ++libdata->ev3.errorCount;
        __enable_irq();
    }
    else
    {
        ++libdata->ev3.heartbeat_counter;
    }
}

SensorLibraryStatus_t EV3_Init(SensorPort_t* sensorPort)
{
    SensorPort_SetVccIo(sensorPort, Sensor_VccIo_5V);

    EV3SensorDriverData_t* libdata = SensorPortHandler_Call_Allocate(sizeof(EV3SensorDriverData_t));
    sensorPort->libraryData = libdata;

    ev3_enter_state(sensorPort, libdata, EV3State_Reset);

    SensorPort_SetGreenLed(sensorPort, true);

    return SensorLibraryStatus_Ok;
}

void EV3_DeInit(SensorPort_t* sensorPort, OnDeInitCompletedCb cb)
{
    SensorPort_SetGreenLed(sensorPort, false);
    SensorPort_SetOrangeLed(sensorPort, false);
    SensorPort_SetVccIo(sensorPort, Sensor_VccIo_3V3);
    SensorPort_UART_Disable(sensorPort);
    SensorPortHandler_Call_Free(&sensorPort->libraryData);
    cb(sensorPort, true);
}

SensorLibraryStatus_t EV3_Update(SensorPort_t* sensorPort)
{
    EV3SensorDriverData_t* libdata = (EV3SensorDriverData_t*) sensorPort->libraryData;

    switch (libdata->ev3.state)
    {
        case EV3State_Reset:
            ev3_run_reset(sensorPort, libdata);
            break;

        case EV3State_ReadType:
            ev3_update_read_type(sensorPort, libdata);
            break;

        case EV3State_Initialize:
            ev3_update_initialize(sensorPort, libdata);
            break;

        case EV3State_Active:
            ev3_update_active(sensorPort, libdata);
            break;

        default:
            ASSERT(0);
            break;
    }

    return SensorLibraryStatus_Ok;
}

SensorLibraryStatus_t EV3_UpdateConfiguration(SensorPort_t* sensorPort, const uint8_t* data, uint8_t size)
{
    if (size != 1u)
    {
        return SensorLibraryStatus_LengthError;
    }
    
    EV3SensorDriverData_t* libdata = (EV3SensorDriverData_t*) sensorPort->libraryData;
    
    uint8_t requested_mode_idx = data[0];
    
    if (requested_mode_idx >= libdata->ev3.nModes)
    {
        return SensorLibraryStatus_ValueError;
    }

    /* it's possible we have to resend confiuration (no ACK for it) so don't check for change */
    ev3_send_mode_switch(sensorPort, libdata, requested_mode_idx);
    libdata->ev3.current_mode = requested_mode_idx;

    libdata->ev3.errorCount = 0u;
    libdata->ev3.heartbeat_counter = 0u;

    /* next data (with new mode) will indicate finished change */
    
    return SensorLibraryStatus_Ok;
}

SensorLibraryStatus_t EV3_UpdateAnalogData(SensorPort_t* sensorPort, uint8_t rawValue)
{
    (void) sensorPort;
    (void) rawValue;
    return SensorLibraryStatus_Ok;
}

SensorLibraryStatus_t EV3_InterruptCallback(SensorPort_t* sensorPort, bool status)
{
    (void) sensorPort;
    (void) status;
    return SensorLibraryStatus_Ok;
}

void EV3_ReadSensorInfo(SensorPort_t* sensorPort, uint8_t page, uint8_t* buffer, uint8_t size, uint8_t* count)
{
    (void) sensorPort;
    (void) page;
    (void) buffer;
    (void) size;

    EV3SensorDriverData_t* libdata = (EV3SensorDriverData_t*) sensorPort->libraryData;

    if (libdata->ev3.state != EV3State_Active)
    {
        *count = 0u;
        return;
    }

    if (page == 0u)
    {
        /* read sensor info */
        buffer[0] = libdata->ev3.sensor_type;
        memcpy(&buffer[1], &libdata->ev3.speed, sizeof(uint32_t));
        buffer[5] = libdata->ev3.nModes;
        buffer[6] = libdata->ev3.nViews;
        *count = 7u;
    }
    else
    {
        uint8_t mode = page - 1u;

        if (mode >= libdata->ev3.nModes)
        {
            *count = 0u;
            return;
        }

        /* read mode info */
        buffer[0] = libdata->ev3.modes[mode].nSamples;
        buffer[1] = libdata->ev3.modes[mode].dataType;
        buffer[2] = libdata->ev3.modes[mode].figures;
        buffer[3] = libdata->ev3.modes[mode].decimals;
        memcpy(&buffer[4], &libdata->ev3.modes[mode].raw_min, 4u);
        memcpy(&buffer[8], &libdata->ev3.modes[mode].raw_max, 4u);
        memcpy(&buffer[12], &libdata->ev3.modes[mode].pct_min, 4u);
        memcpy(&buffer[16], &libdata->ev3.modes[mode].pct_max, 4u);
        memcpy(&buffer[20], &libdata->ev3.modes[mode].si_min, 4u);
        memcpy(&buffer[24], &libdata->ev3.modes[mode].si_max, 4u);

        *count = 28u;
    }
}

static bool EV3_TestSensorOnPort(SensorPort_t *port, SensorOnPortStatus_t *result)
{
  *result = SensorOnPortStatus_Unknown;
  return true;
}

static const SensorLibrary_t sensor_library_ev3 =
{
    .name                = "EV3",
    .Init                = &EV3_Init,
    .DeInit              = &EV3_DeInit,
    .Update              = &EV3_Update,
    .UpdateConfiguration = &EV3_UpdateConfiguration,
    .UpdateAnalogData    = &EV3_UpdateAnalogData,
    .InterruptHandler    = &EV3_InterruptCallback,
    .ReadSensorInfo      = &EV3_ReadSensorInfo,
    .TestSensorOnPort    = &EV3_TestSensorOnPort
};

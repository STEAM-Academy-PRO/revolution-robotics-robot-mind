#include "ev3_lib.h"

#include "utils.h"
#include "utils_assert.h"

/* return the package length, including header, crc */
uint8_t ev3_command_length(uint8_t byte)
{
    uint8_t category = byte & 0xC0u;
    if (category == 0x00u)
    {
        return 1u;
    }

    uint8_t shift = (byte >> 3u) & 0x07u;
    uint8_t length = 1u << shift;

    if (category == 0x80u)
    {
        /* info byte */
        ++length;
    }

    return length + 2u; /* cmd, crc */
}

EV3Message_t ev3_get_message_type(uint8_t byte)
{
    uint8_t category = byte & 0xC0u;
    uint8_t mode = byte & 0x07u;

    switch (category)
    {
        case 0x00u: /* System */
            switch (mode)
            {
                case 0x00u: return EV3Message_Sync;
                case 0x02u: return EV3Message_Invalid;
                case 0x04u: return EV3Message_Ack;
                case 0x06u: return EV3Message_Esc;

                default:
                    break;
            }
            break;

        case 0x40u: /* Command */
            switch (mode)
            {
                case 0x00u: return EV3Message_Type;
                case 0x01u: return EV3Message_Modes;
                case 0x02u: return EV3Message_Speed;
                case 0x03u: return EV3Message_Invalid;
                case 0x04u: return EV3Message_Invalid;

                default:
                    break;
            }
            break;

        case 0x80u: return EV3Message_Info;
        case 0xC0u: return EV3Message_Data;

        default:
            ASSERT(0);
            break;
    }

    return EV3Message_Invalid;
}

bool ev3_provides_wrong_crc(EV3Instance_t* libdata, uint8_t header_byte)
{
    if (libdata->sensor_type == 29u)
    {
        if (header_byte == 0xDCu)
        {
            return true;
        }
    }

    return false;
}

bool ev3_check_crc(const uint8_t* buffer, size_t length)
{
    if (length > 1u)
    {
        uint8_t crc = 0xFFu;
        for (size_t i = 0u; i < length - 1u; i++)
        {
            crc ^= buffer[i];
        }

        if (crc != buffer[length - 1u])
        {
            return false;
        }
    }

    return true;
}

size_t ev3_count_initialized_modes(EV3Instance_t* instance)
{
    size_t initialized = 0u;
    for (size_t i = 0u; i < ARRAY_SIZE(instance->modes); i++)
    {
        if (instance->modes[i].dataType != EV3Data_invalid)
        {
            ++initialized;
        }
    }

    return initialized;
}

bool ev3_process_mode_format(EV3Mode_t* mode, uint8_t* buffer)
{    
    mode->nSamples = buffer[2];

    mode->figures = buffer[4];
    mode->decimals = buffer[5];

    switch(buffer[3])
    {
        case 0:
            mode->rawSize = mode->nSamples;
            mode->dataType = EV3Data_int8;
            break;

        case 1:
            mode->rawSize = 2 * mode->nSamples;
            mode->dataType = EV3Data_int16;
            break;

        case 2:
            mode->rawSize = 4 * mode->nSamples;
            mode->dataType = EV3Data_int32;
            break;

        case 3:
            mode->rawSize = 4 * mode->nSamples;
            mode->dataType = EV3Data_float;
            break;

        default:
            return false;
    }

    return true;
}
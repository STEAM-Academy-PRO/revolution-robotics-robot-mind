#include "converter.h"

int32_t get_int32(const uint8_t* buffer)
{
    return *(int32_t*) buffer;
}

uint32_t get_uint32(const uint8_t* buffer)
{
    return *(uint32_t*) buffer;
}

int16_t get_int16(const uint8_t* buffer)
{
    return *(int16_t*) buffer;
}

uint16_t get_uint16(const uint8_t* buffer)
{
    return *(uint16_t*) buffer;
}

float get_float(const uint8_t* buffer)
{
    return *(float*) buffer;
}

/*
 * converter.c
 *
 * Created: 2019. 04. 26. 13:46:33
 *  Author: Dániel Buga
 */ 

#include "converter.h"
#include <string.h>

int32_t get_int32(const uint8_t* buffer)
{
    int32_t result;
    memcpy(&result, buffer, sizeof(result));
    return result;
}

int16_t get_int16(const uint8_t* buffer)
{
    int16_t result;
    memcpy(&result, buffer, sizeof(result));
    return result;
}

uint16_t get_uint16(const uint8_t* buffer)
{
    uint16_t result;
    memcpy(&result, buffer, sizeof(result));
    return result;
}

uint32_t get_uint32(const uint8_t* buffer)
{
    uint32_t result;
    memcpy(&result, buffer, sizeof(result));
    return result;
}

float get_float(const uint8_t* buffer)
{
    float result;
    memcpy(&result, buffer, sizeof(result));
    return result;
}

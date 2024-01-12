/*
 * converter.h
 *
 * Created: 4/4/2019 2:25:55 PM
 *  Author: Daniel Buga
 */ 


#ifndef CONVERTER_H_
#define CONVERTER_H_

#include <stdint.h>

int32_t get_int32(const uint8_t* buffer);
int16_t get_int16(const uint8_t* buffer);
uint16_t get_uint16(const uint8_t* buffer);
uint32_t get_uint32(const uint8_t* buffer);
float get_float(const uint8_t* buffer);

#endif /* CONVERTER_H_ */

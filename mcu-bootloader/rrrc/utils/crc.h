/*
 * crc.h
 *
 * Created: 06/05/2019 13:33:09
 *  Author: Dániel Buga
 */ 


#ifndef UTILS_CRC_H_
#define UTILS_CRC_H_

#include <stdint.h>
#include <stdio.h>

uint8_t CRC7_Calculate(uint8_t crc, const uint8_t* pBuffer, size_t size);
uint16_t CRC16_Calculate(uint16_t crc, const uint8_t* pBuffer, size_t size);

#endif /* CRC_H_ */

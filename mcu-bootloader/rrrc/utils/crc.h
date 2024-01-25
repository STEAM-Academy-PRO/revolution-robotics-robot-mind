#ifndef UTILS_CRC_H_
#define UTILS_CRC_H_

#include <stdint.h>
#include <stdio.h>

void CRC32_Init(void);

uint8_t CRC7_Calculate(uint8_t crc, const uint8_t* pBuffer, size_t size);
uint16_t CRC16_Calculate(uint16_t crc, const uint8_t* pBuffer, size_t size);
uint32_t CRC32_Calculate(uint32_t crc32, const uint8_t* pBuffer, size_t size);

#endif /* CRC_H_ */

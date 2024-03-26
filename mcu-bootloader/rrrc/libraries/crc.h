#ifndef UTILS_CRC_H_
#define UTILS_CRC_H_

#include <stdint.h>
#include <stdio.h>

void CRC32_Init(void);
uint32_t CRC32_Calculate(uint32_t crc32, const uint8_t* pBuffer, size_t size);

#endif /* CRC_H_ */

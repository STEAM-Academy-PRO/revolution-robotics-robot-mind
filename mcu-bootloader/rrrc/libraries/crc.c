#include "crc.h"

#include <stdbool.h>

static uint32_t crc32_table[256];

void CRC32_Init(void)
{
    #define CRC32_POLYNOMIAL (0xEDB88320)

    for (int idx = 0; idx < 256; idx++)
    {
        uint8_t bit = 8;
        uint32_t val = idx;
        do
        {
            val = (val & 1) ? ((val >> 1) ^ CRC32_POLYNOMIAL) : (val >> 1);
        } while (--bit);
        crc32_table[idx] = val;
    }
}

uint32_t CRC32_Calculate(uint32_t crc, const uint8_t* pBuffer, size_t size)
{
    while (size-- > 0u)
    {
        crc = crc32_table[(crc ^ *pBuffer++) & 0xFF] ^ (crc >> 8);
    }

    return crc;
}

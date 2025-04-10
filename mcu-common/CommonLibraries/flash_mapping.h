#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include "driver_init.h"

#define FLASH_AVAILABLE     ((FLASH_SIZE / 2) - NVMCTRL_BLOCK_SIZE)
#define FLASH_FW_OFFSET     (FLASH_SIZE / 2)
#define FLASH_HDR_OFFSET    (FLASH_FW_OFFSET + FLASH_AVAILABLE) // the last 0x2000

typedef struct
{
    uint32_t hw_version;
    uint32_t bootloader_version;
    uint32_t target_checksum;
    uint32_t target_length;
} ApplicationFlashHeader_t;

#define FLASH_HEADER  ((ApplicationFlashHeader_t*) (FLASH_HDR_OFFSET))

typedef enum {
    StartupReason_PowerUp,
    StartupReason_BootloaderRequest,
    StartupReason_WatchdogReset,
    StartupReason_BrownOutReset,
} StartupReason_t;

StartupReason_t FMP_CheckBootloaderModeRequest (void);

uint32_t FMP_ReadApplicationChecksum(void);
bool FMP_FlashHeaderValid(void);
uint32_t FMP_RecordedFirmwareCRC(void);
uint32_t FMP_CalculateFirmwareCRC(void);
bool FMP_IsApplicationEmpty(void);
bool FMP_IsApplicationHeaderEmpty(void);

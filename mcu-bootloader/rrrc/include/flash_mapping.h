//==============================================================================
// flash_mapping.h
//
// Created: 10.05.2019 15:49:09
//  Author: pkurganov
//==============================================================================

#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include "driver_init.h"

#define FLASH_AVAILABLE     ((FLASH_SIZE / 2) - NVMCTRL_BLOCK_SIZE)
#define FLASH_FW_OFFSET     (FLASH_SIZE / 2)
#define FLASH_HDR_OFFSET    (FLASH_FW_OFFSET + FLASH_AVAILABLE)

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
    StartupReason_WatchdogReset
} StartupReason_t;

//------------------------------------------------------------------------------
//------------------------------------------------------------------------------
StartupReason_t FMP_CheckBootloaderModeRequest (void);

//------------------------------------------------------------------------------
//------------------------------------------------------------------------------
uint32_t FMP_ReadApplicationChecksum(void);

//------------------------------------------------------------------------------
//------------------------------------------------------------------------------
bool FMP_CheckTargetFirmware (bool check_expected_crc, uint32_t expected_crc);

//------------------------------------------------------------------------------
//------------------------------------------------------------------------------
bool FMP_IsApplicationEmpty(void);
bool FMP_IsApplicationHeaderEmpty(void);

//------------------------------------------------------------------------------
//------------------------------------------------------------------------------
void FMP_FixApplicationHeader(void);

//------------------------------------------------------------------------------
//------------------------------------------------------------------------------
void FMT_JumpTargetFirmware (void);

//------------------------------------------------------------------------------
//------------------------------------------------------------------------------
void FMT_SetBootloaderRequest(void);

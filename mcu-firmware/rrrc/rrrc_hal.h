/*
 * worklogic.h
 *
 * Created: 1/4/2019 8:22:31 PM
 *  Author: User
 */ 


#ifndef RRRC_HAL_H_
#define RRRC_HAL_H_

#include "driver_init.h"
#include "FreeRTOS.h"
#include "task.h"
#include "semphr.h"

#define FLASH_AVAILABLE     ((FLASH_SIZE / 2) - NVMCTRL_BLOCK_SIZE)
#define FLASH_FW_OFFSET     (FLASH_SIZE / 2)
#define FLASH_HDR_OFFSET    (FLASH_FW_OFFSET + FLASH_AVAILABLE)

typedef struct 
{
    uint32_t hw_version;
    uint32_t bootloader_version;
    uint32_t target_checksum;
    uint32_t target_length;
} AppFlashHeader_t;

#define FLASH_HEADER  ((AppFlashHeader_t*) (FLASH_HDR_OFFSET))

#endif /* RRRC_HAL_H_ */
#include "UpdateManager.h"
#include "utils/crc.h"

#include "../../utils/functions.h"
#include <math.h>

static bool isInitialized = false;
static uint32_t expected_crc;
static uint32_t current_crc;
static size_t total_length;
static size_t current_length;

static uint8_t page[NVMCTRL_PAGE_SIZE];
static size_t pageWrIdx = 0u;
static size_t nvmOffset = 0u;

static void _flush(void)
{
    if (pageWrIdx > 0u)
    {
        flash_append(&FLASH_0, nvmOffset, page, pageWrIdx);
        nvmOffset += pageWrIdx;
        pageWrIdx = 0u;
    }
}

static void _select_start_addr(size_t start_addr)
{
    _flush();

    pageWrIdx = 0u;
    nvmOffset = start_addr;
}

static void _program_byte(uint8_t data)
{
    page[pageWrIdx++] = data;
    if (pageWrIdx == NVMCTRL_PAGE_SIZE)
    {
        _flush();
    }
}

static void _program_bytes(const uint8_t* pData, size_t dataSize)
{
    while (dataSize-- > 0u)
    {
        _program_byte(*pData);
        ++pData;
    }
}

bool UpdateManager_Run_CheckImageFitsInFlash(size_t size)
{
    return size <= FLASH_AVAILABLE;
}

void UpdateManager_Run_InitializeUpdate(size_t firmware_size, uint32_t checksum)
{
    isInitialized = true;
    expected_crc = checksum;
    total_length = firmware_size;
    current_crc = 0xFFFFFFFFu;
    current_length = 0u;
    pageWrIdx = 0u;

    ApplicationFlashHeader_t header = {
        .bootloader_version = BOOTLOADER_VERSION,
        .hw_version = HARDWARE_VERSION,
        .target_checksum = checksum,
        .target_length = firmware_size
    };

    UpdateManager_Write_Progress(0u);

    UpdateManager_Run_UpdateApplicationHeader(&header);
    
    /* Initialize the write parameters and erase firmware block in flash memory */
    flash_erase(&FLASH_0, FLASH_FW_OFFSET, FLASH_AVAILABLE / NVMCTRL_PAGE_SIZE);
    _select_start_addr(FLASH_FW_OFFSET);
}

UpdateManager_Status_t UpdateManager_Run_Program(const uint8_t* pData, size_t chunkSize)
{
    if (!isInitialized)
    {
        return UpdateManager_Not_Initialized;
    }

    /* update checksum */
    current_crc = CRC32_Calculate(current_crc, pData, chunkSize);
    current_length += chunkSize;
    
    /* program flash */
    _program_bytes(pData, chunkSize);
    
    UpdateManager_Write_Progress(lroundf(map(current_length, 0, total_length, 0, 255)));

    return UpdateManager_Ok;
}

UpdateManager_Status_t UpdateManager_Run_Finalize(void)
{
    /* if not initialized, try to reboot to application */
    if (isInitialized)
    {
        _flush();

        if (current_length != total_length)
        {
            return UpdateManager_Error_ImageInvalid;
        }
    
        if (!FMP_CheckTargetFirmware(true, expected_crc))
        {
            return UpdateManager_Error_ImageInvalid;
        }
    }

    /* Reset here - firmware will be loaded at the beginning of the bootloader execution */
    NVIC_SystemReset();

    /* this will not be reached */
    return UpdateManager_Ok;
}

void UpdateManager_Run_UpdateApplicationHeader(const ApplicationFlashHeader_t* header)
{
    /* Also erase the block that stores the firmware header and store the header */
    flash_erase(&FLASH_0, FLASH_HDR_OFFSET, NVMCTRL_BLOCK_SIZE / NVMCTRL_PAGE_SIZE);

    _select_start_addr(FLASH_HDR_OFFSET);
    _program_bytes((uint8_t*) header, sizeof(ApplicationFlashHeader_t));
    _flush();
}

__attribute__((weak))
void UpdateManager_Write_Progress(uint8_t progress)
{
    (void) progress;
    /* nothing to do */
}

#include "UpdateManager.h"
#include "utils.h"

/* Begin User Code Section: Declarations */
#include "CommonLibraries/log.h"

#include "CommonLibraries/functions.h"
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
/* End User Code Section: Declarations */

bool UpdateManager_Run_CheckImageFitsInFlash(uint32_t image_size)
{
    /* Begin User Code Section: CheckImageFitsInFlash:run Start */
    return image_size <= FLASH_AVAILABLE;
    /* End User Code Section: CheckImageFitsInFlash:run Start */
    /* Begin User Code Section: CheckImageFitsInFlash:run End */

    /* End User Code Section: CheckImageFitsInFlash:run End */
}

void UpdateManager_Run_InitializeUpdate(uint32_t firmware_size, uint32_t checksum)
{
    /* Begin User Code Section: InitializeUpdate:run Start */
    LOG_RAW("Initializing update\n");

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

    UpdateManager_RaiseEvent_ProgressChanged(0u);

    UpdateManager_Run_UpdateApplicationHeader(&header);

    /* Initialize the write parameters and erase firmware block in flash memory */
    flash_erase(&FLASH_0, FLASH_FW_OFFSET, FLASH_AVAILABLE / NVMCTRL_PAGE_SIZE);
    _select_start_addr(FLASH_FW_OFFSET);
    /* End User Code Section: InitializeUpdate:run Start */
    /* Begin User Code Section: InitializeUpdate:run End */

    /* End User Code Section: InitializeUpdate:run End */
}

UpdateManager_Status_t UpdateManager_Run_WriteNextChunk(ConstByteArray_t data)
{
    /* Begin User Code Section: WriteNextChunk:run Start */
    if (!isInitialized)
    {
        return UpdateManager_Not_Initialized;
    }

    /* update checksum */
    current_crc = UpdateManager_Call_Calculate_CRC32(current_crc, data);
    current_length += data.count;

    /* program flash */
    _program_bytes(data.bytes, data.count);

    UpdateManager_RaiseEvent_ProgressChanged(lroundf(map(current_length, 0, total_length, 0, 255)));

    return UpdateManager_Ok;
    /* End User Code Section: WriteNextChunk:run Start */
    /* Begin User Code Section: WriteNextChunk:run End */

    /* End User Code Section: WriteNextChunk:run End */
}

UpdateManager_Status_t UpdateManager_Run_Finalize(void)
{
    /* Begin User Code Section: Finalize:run Start */
    /* if not initialized, try to reboot to application */
    if (isInitialized)
    {
        _flush();

        if (current_length != total_length)
        {
            return UpdateManager_Error_ImageInvalid;
        }

        bool crc_ok = FMP_FlashHeaderValid();

        if (!crc_ok)
        {
            LOG_RAW("Invalid firmware header\n");
        }
        else
        {
            uint32_t calculated_crc = FMP_CalculateFirmwareCRC();
            uint32_t recorded_crc = FMP_RecordedFirmwareCRC();

            if (recorded_crc != expected_crc)
            {
                LOG("Firmware checksum mismatch: recorded %X, expected %X\n", recorded_crc, expected_crc);
                crc_ok = false;
            }
            else if (calculated_crc != expected_crc)
            {
                LOG("Firmware CRC mismatch: calculated %X, expected %X\n", calculated_crc, expected_crc);
                crc_ok = false;
            }
        }

        if (!crc_ok)
        {
            return UpdateManager_Error_ImageInvalid;
        }
    }

    /* Reset here - firmware will be loaded at the beginning of the bootloader execution */
    NVIC_SystemReset();

    /* this will not be reached */
    return UpdateManager_Ok;
    /* End User Code Section: Finalize:run Start */
    /* Begin User Code Section: Finalize:run End */

    /* End User Code Section: Finalize:run End */
}

void UpdateManager_Run_UpdateApplicationHeader(const ApplicationFlashHeader_t* header)
{
    /* Begin User Code Section: UpdateApplicationHeader:run Start */
    /* Also erase the block that stores the firmware header and store the header */
    flash_erase(&FLASH_0, FLASH_HDR_OFFSET, NVMCTRL_BLOCK_SIZE / NVMCTRL_PAGE_SIZE);

    _select_start_addr(FLASH_HDR_OFFSET);
    _program_bytes((uint8_t*) header, sizeof(ApplicationFlashHeader_t));
    _flush();
    /* End User Code Section: UpdateApplicationHeader:run Start */
    /* Begin User Code Section: UpdateApplicationHeader:run End */

    /* End User Code Section: UpdateApplicationHeader:run End */
}

__attribute__((weak))
void UpdateManager_RaiseEvent_ProgressChanged(uint8_t progress)
{
    (void) progress;
    /* Begin User Code Section: ProgressChanged:run Start */

    /* End User Code Section: ProgressChanged:run Start */
    /* Begin User Code Section: ProgressChanged:run End */

    /* End User Code Section: ProgressChanged:run End */
}

__attribute__((weak))
uint32_t UpdateManager_Call_Calculate_CRC32(uint32_t init_value, ConstByteArray_t data)
{
    (void) data;
    (void) init_value;
    /* Begin User Code Section: Calculate_CRC32:run Start */

    /* End User Code Section: Calculate_CRC32:run Start */
    /* Begin User Code Section: Calculate_CRC32:run End */

    /* End User Code Section: Calculate_CRC32:run End */
    return 0u;
}

#include "VersionProvider.h"
#include "utils.h"

/* Begin User Code Section: Declarations */
#include "fw_version.h"
#include "rrrc_hal.h"

#include <string.h>

#define FIRMWARE_VERSION_STRING "0.2." FW_VERSION

/* App header info, as defined (and written) in the bootloader */
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
/* End User Code Section: Declarations */

uint32_t VersionProvider_Constant_FirmwareVersion(void)
{
    /* Begin User Code Section: FirmwareVersion:constant Start */

    /* End User Code Section: FirmwareVersion:constant Start */
    /* Begin User Code Section: FirmwareVersion:constant End */

    /* End User Code Section: FirmwareVersion:constant End */
    return FW_VERSION_NUMBER;
}

ByteArray_t VersionProvider_Constant_FirmwareVersionString(void)
{
    /* Begin User Code Section: FirmwareVersionString:constant Start */

    /* End User Code Section: FirmwareVersionString:constant Start */
    /* Begin User Code Section: FirmwareVersionString:constant End */

    /* End User Code Section: FirmwareVersionString:constant End */
    return (ByteArray_t) {.bytes = (uint8_t*) FIRMWARE_VERSION_STRING, .count = strlen(FIRMWARE_VERSION_STRING) };
}

uint32_t VersionProvider_Constant_HardwareVersion(void)
{
    /* Begin User Code Section: HardwareVersion:constant Start */

    /* End User Code Section: HardwareVersion:constant Start */
    /* Begin User Code Section: HardwareVersion:constant End */

    /* End User Code Section: HardwareVersion:constant End */
    return FLASH_HEADER->hw_version;
}

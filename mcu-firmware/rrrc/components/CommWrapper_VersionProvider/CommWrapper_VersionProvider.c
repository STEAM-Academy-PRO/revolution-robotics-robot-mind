#include "CommWrapper_VersionProvider.h"
#include "utils.h"

/* Begin User Code Section: Declarations */
#include "utils_assert.h"
#include "fw_version.h"

#include <string.h>

static const char* hw_version_strings[] =
{
    "1.0.0",
    "1.0.1",
    "2.0.0"
};
/* End User Code Section: Declarations */

Comm_Status_t CommWrapper_VersionProvider_Run_Command_ReadHardwareVersion_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount)
{
    /* Begin User Code Section: Command_ReadHardwareVersion_Start:run Start */
    if (commandPayload.count != 0u)
    {
        return Comm_Status_Error_PayloadLengthError;
    }

    uint32_t hw = CommWrapper_VersionProvider_Read_HardwareVersion();

    if (hw < ARRAY_SIZE(hw_version_strings))
    {
        size_t len = strlen(hw_version_strings[hw]);
        ASSERT(response.count >= len);
        memcpy(response.bytes, hw_version_strings[hw], len);
        *responseCount = len;

        return Comm_Status_Ok;
    }
    else
    {
        return Comm_Status_Error_InternalError;
    }
    /* End User Code Section: Command_ReadHardwareVersion_Start:run Start */
    /* Begin User Code Section: Command_ReadHardwareVersion_Start:run End */

    /* End User Code Section: Command_ReadHardwareVersion_Start:run End */
}

Comm_Status_t CommWrapper_VersionProvider_Run_Command_ReadFirmwareVersion_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount)
{
    /* Begin User Code Section: Command_ReadFirmwareVersion_Start:run Start */
    if (commandPayload.count != 0u)
    {
        return Comm_Status_Error_PayloadLengthError;
    }

    ByteArray_t version = CommWrapper_VersionProvider_Read_FirmwareVersionString();
    ASSERT(response.count >= version.count);

    memcpy(response.bytes, version.bytes, version.count);
    *responseCount = version.count;

    return Comm_Status_Ok;
    /* End User Code Section: Command_ReadFirmwareVersion_Start:run Start */
    /* Begin User Code Section: Command_ReadFirmwareVersion_Start:run End */

    /* End User Code Section: Command_ReadFirmwareVersion_Start:run End */
}

__attribute__((weak))
ByteArray_t CommWrapper_VersionProvider_Read_FirmwareVersionString(void)
{
    /* Begin User Code Section: FirmwareVersionString:read Start */

    /* End User Code Section: FirmwareVersionString:read Start */
    /* Begin User Code Section: FirmwareVersionString:read End */

    /* End User Code Section: FirmwareVersionString:read End */
    return (ByteArray_t) {.bytes = (uint8_t*) "", .count = 0u };
}

__attribute__((weak))
uint32_t CommWrapper_VersionProvider_Read_HardwareVersion(void)
{
    /* Begin User Code Section: HardwareVersion:read Start */

    /* End User Code Section: HardwareVersion:read Start */
    /* Begin User Code Section: HardwareVersion:read End */

    /* End User Code Section: HardwareVersion:read End */
    return 0u;
}

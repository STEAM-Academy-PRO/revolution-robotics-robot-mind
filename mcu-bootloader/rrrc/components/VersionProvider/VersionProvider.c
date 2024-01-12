/*
 * VersionProvider.c
 *
 * Created: 2019. 07. 25. 14:38:17
 *  Author: Dániel Buga
 */ 

#include "VersionProvider.h"

#include "utils.h"
#include <string.h>

static const char* hw_version_strings[] = 
{
    "1.0.0",
    "1.0.1",
    "2.0.0"
};

Comm_Status_t VersionProvider_GetHardwareVersion_Start(const uint8_t* commandPayload, uint8_t commandSize, uint8_t* response, uint8_t responseBufferSize, uint8_t* responseCount)
{
    uint32_t hw = HARDWARE_VERSION;

    if (hw < ARRAY_SIZE(hw_version_strings))
    {
        uint8_t len = strlen(hw_version_strings[hw]);
        memcpy(response, hw_version_strings[hw], len);
        *responseCount = len;
    
        return Comm_Status_Ok;
    }
    else
    {
        return Comm_Status_Error_InternalError;
    }
}

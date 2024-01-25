#ifndef UPDATEMANAGER_H_
#define UPDATEMANAGER_H_

#include <stdint.h>
#include <stdbool.h>

#include "flash_mapping.h"

typedef enum 
{
    UpdateManager_Ok,
    UpdateManager_Not_Initialized,
    UpdateManager_Error_ImageInvalid,
} UpdateManager_Status_t;

bool UpdateManager_Run_CheckImageFitsInFlash(size_t size);
void UpdateManager_Run_InitializeUpdate(size_t firmware_size, uint32_t checksum);
UpdateManager_Status_t UpdateManager_Run_Program(const uint8_t* pData, size_t chunkSize);
UpdateManager_Status_t UpdateManager_Run_Finalize(void);

void UpdateManager_Run_UpdateApplicationHeader(const ApplicationFlashHeader_t* header);
void UpdateManager_Write_Progress(uint8_t progress);

#endif /* UPDATEMANAGER_H_ */

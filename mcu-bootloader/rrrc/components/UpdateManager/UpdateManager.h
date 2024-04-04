#ifndef COMPONENT_UPDATE_MANAGER_H_
#define COMPONENT_UPDATE_MANAGER_H_

#ifndef COMPONENT_TYPES_UPDATE_MANAGER_H_
#define COMPONENT_TYPES_UPDATE_MANAGER_H_

#include "flash_mapping.h"
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>


typedef enum {
    UpdateManager_Ok,
    UpdateManager_Not_Initialized,
    UpdateManager_Error_ImageInvalid
} UpdateManager_Status_t;

typedef struct {
    const uint8_t* bytes;
    size_t count;
} ConstByteArray_t;

#endif /* COMPONENT_TYPES_UPDATE_MANAGER_H_ */

/* Begin User Code Section: Declarations */

/* End User Code Section: Declarations */

bool UpdateManager_Run_CheckImageFitsInFlash(uint32_t image_size);
void UpdateManager_Run_InitializeUpdate(uint32_t firmware_size, uint32_t checksum);
UpdateManager_Status_t UpdateManager_Run_WriteNextChunk(ConstByteArray_t data);
UpdateManager_Status_t UpdateManager_Run_Finalize(void);
void UpdateManager_Run_UpdateApplicationHeader(const ApplicationFlashHeader_t* header);
void UpdateManager_RaiseEvent_ProgressChanged(uint8_t progress);

#endif /* COMPONENT_UPDATE_MANAGER_H_ */

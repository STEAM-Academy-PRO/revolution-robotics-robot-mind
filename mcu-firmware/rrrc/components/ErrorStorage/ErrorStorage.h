#ifndef COMPONENT_ERROR_STORAGE_H_
#define COMPONENT_ERROR_STORAGE_H_

#ifndef COMPONENT_TYPES_ERROR_STORAGE_H_
#define COMPONENT_TYPES_ERROR_STORAGE_H_

#include "components/ErrorStorage/ErrorStorageTypes.h"
#include <stdbool.h>
#include <stdint.h>


#endif /* COMPONENT_TYPES_ERROR_STORAGE_H_ */

void ErrorStorage_Run_OnInit(void);
void ErrorStorage_Run_Store(const ErrorInfo_t* data);
bool ErrorStorage_Run_Read(uint32_t index, ErrorInfo_t* data);
void ErrorStorage_Run_Clear(void);
void ErrorStorage_Write_NumberOfStoredErrors(uint32_t value);
uint32_t ErrorStorage_Read_FirmwareVersion(void);
uint32_t ErrorStorage_Read_HardwareVersion(void);

#endif /* COMPONENT_ERROR_STORAGE_H_ */

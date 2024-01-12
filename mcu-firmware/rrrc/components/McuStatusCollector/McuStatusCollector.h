#ifndef COMPONENT_MCU_STATUS_COLLECTOR_H_
#define COMPONENT_MCU_STATUS_COLLECTOR_H_

#ifndef COMPONENT_TYPES_MCU_STATUS_COLLECTOR_H_
#define COMPONENT_TYPES_MCU_STATUS_COLLECTOR_H_

#include <stdint.h>
#include <stdio.h>


typedef struct {
    uint8_t* bytes;
    size_t count;
} ByteArray_t;

typedef struct {
    ByteArray_t data;
    uint8_t version;
} SlotData_t;

#endif /* COMPONENT_TYPES_MCU_STATUS_COLLECTOR_H_ */

void McuStatusCollector_Run_Reset(void);
uint8_t McuStatusCollector_Run_Read(ByteArray_t destination);
void McuStatusCollector_Run_EnableSlot(uint8_t slot);
void McuStatusCollector_Run_DisableSlot(uint8_t slot);
SlotData_t McuStatusCollector_Read_SlotData(uint32_t index);

#endif /* COMPONENT_MCU_STATUS_COLLECTOR_H_ */

#ifndef COMPONENT_CRC_H_
#define COMPONENT_CRC_H_

#ifndef COMPONENT_TYPES_CRC_H_
#define COMPONENT_TYPES_CRC_H_

#include <stdint.h>
#include <stdio.h>


typedef struct {
    const uint8_t* bytes;
    size_t count;
} ConstByteArray_t;

#endif /* COMPONENT_TYPES_CRC_H_ */

/* Begin User Code Section: Declarations */

/* End User Code Section: Declarations */

uint8_t CRC_Run_Calculate_CRC7(uint8_t init_value, ConstByteArray_t data);
uint16_t CRC_Run_Calculate_CRC16(uint16_t init_value, ConstByteArray_t data);

#endif /* COMPONENT_CRC_H_ */

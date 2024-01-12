#ifndef ERROR_INFO_TYPE_H_
#define ERROR_INFO_TYPE_H_

#include <stdint.h>

typedef struct __attribute__((packed)) {
    uint8_t error_id;
    uint32_t hardware_version;
    uint32_t firmware_version;
    uint8_t data[54];
} ErrorInfo_t;

#endif /* ERROR_INFO_TYPE_H_ */

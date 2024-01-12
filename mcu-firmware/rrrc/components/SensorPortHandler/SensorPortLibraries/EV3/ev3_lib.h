#ifndef EV3_LIB_H_
#define EV3_LIB_H_

#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>

#define MAX_MODES       8
#define HEARTBEAT_LIMIT 14    /**< x20ms update time -> NACK every 300ms, just like the EV3 brick */

#define ERROR_THRESHOLD 10

enum InfoTypes {
    INFO_NAME = 0,
    INFO_RAW,
    INFO_PCT,
    INFO_SI,
    INFO_UNITS,
    INFO_FORMAT = 0x80
};

typedef enum {
    EV3State_Reset,
    EV3State_ReadType,
    EV3State_Initialize,
    EV3State_Active
} EV3State_t;

typedef enum {
    EV3Data_int8,
    EV3Data_int16,
    EV3Data_int32,
    EV3Data_float,
    EV3Data_invalid
} EV3DataType_t;

typedef struct {
    uint8_t nSamples;
    uint8_t rawSize;
    EV3DataType_t dataType;
	float raw_min;
	float raw_max;
	float pct_min;
	float pct_max;
	float si_min;
	float si_max;
    uint8_t figures;
    uint8_t decimals;
} EV3Mode_t;

typedef enum {
    EV3Message_Sync,
    EV3Message_Ack,
    EV3Message_Esc,
    EV3Message_Type,
    EV3Message_Modes,
    EV3Message_Speed,
    EV3Message_Info,
    EV3Message_Data,
    EV3Message_Invalid
} EV3Message_t;

typedef struct {
    EV3State_t state;
    uint8_t sensor_type;
    uint32_t speed;
    uint8_t heartbeat_counter;
    EV3Mode_t modes[MAX_MODES];
    uint8_t nModes;
    uint8_t nViews;
    uint8_t current_mode;
    uint8_t rxBuffer[128];
    uint8_t dataBuffer[40];
    uint8_t rxBufferRIdx;
    uint8_t rxBufferCount;
    uint8_t errorCount;
} EV3Instance_t;

uint8_t ev3_command_length(uint8_t byte);
EV3Message_t ev3_get_message_type(uint8_t byte);
bool ev3_provides_wrong_crc(EV3Instance_t* libdata, uint8_t header_byte);
bool ev3_check_crc(const uint8_t* buffer, size_t length);
size_t ev3_count_initialized_modes(EV3Instance_t* instance);
bool ev3_process_mode_format(EV3Mode_t* mode, uint8_t* buffer);

#endif /* EV3_LIB_H */

#ifdef DEBUG_LOG

#include "SEGGER_RTT.h"

#define LOG_INIT() SEGGER_RTT_ConfigUpBuffer(0, NULL, NULL, 0, SEGGER_RTT_MODE_NO_BLOCK_SKIP);
#define LOG(...) SEGGER_RTT_printf(0, __VA_ARGS__)
#define LOG_RAW(string) SEGGER_RTT_WriteString(0, (string))

#else

#define LOG_INIT()
#define LOG(...)
#define LOG_RAW(...)

#endif
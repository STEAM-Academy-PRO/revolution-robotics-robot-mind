#include "driver_init.h"
#include "rrrc_hal.h"
#include "rrrc_worklogic.h"
#include "error_ids.h"

#include <string.h>

#include "SEGGER_RTT.h"

static TaskHandle_t xRRRC_Main_xTask;

extern uint32_t _srtt;
extern uint32_t _ertt;

static void clear_rtt() {
    // Try to detect if RTT is initialized. If not, clear the memory area

    static const char _aInitStr[] = "\0\0\0\0\0\0TTR REGGES"; // Reversed to avoid accidentally finding it in RAM

    volatile SEGGER_RTT_CB* p = (volatile SEGGER_RTT_CB*)((char*)&_SEGGER_RTT + SEGGER_RTT_UNCACHED_OFF);

    bool rtt_initialized = true;
    for (uint32_t i = 0; i < sizeof(_aInitStr) - 1; ++i) {
        if (p->acID[i] != _aInitStr[sizeof(_aInitStr) - 2 - i]) {
            rtt_initialized = false;
            break;
        }
    }

    if (!rtt_initialized) {
        // Clear the rtt segments so INIT can be called again
        for (uint32_t* pDest = &_srtt; pDest < &_ertt;) {
            *pDest++ = 0;
        }
    }
}

/**
 * Put functions here to prevent Link-time optimization to remove them
 */
__attribute__((used,optimize("O0")))
void ltoFunctionKeeper(void)
{
    vTaskSwitchContext();
}

int main(void)
{
    clear_rtt();
    SEGGER_RTT_ConfigUpBuffer(0, NULL, NULL, 0, SEGGER_RTT_MODE_NO_BLOCK_SKIP);

    SEGGER_RTT_WriteString(0, "Starting application\r\n");

    RRRC_ProcessLogic_Init();

    BaseType_t success = xTaskCreate(&RRRC_ProcessLogic_xTask, "Main", 1024u, NULL, taskPriority_Main, &xRRRC_Main_xTask);
    configASSERT(success == pdPASS);

    vTaskStartScheduler();
    configASSERT(0);
}

static void _stop(void)
{
    __disable_irq();
    __BKPT(1);
    while (1);
}

void assert_failed(const char *file, uint32_t line)
{
    static bool in_assert = false;

    if (!in_assert)
    {
        SEGGER_RTT_printf(0, "Assertion failed: %s:%d\r\n", file, line);
        in_assert = true;
        ErrorInfo_t data = {
            .error_id = ERROR_ID_ASSERTION_FAILURE
        };

        memset(&data.data[0], 0u, sizeof(data.data));
        memcpy(&data.data[0], &line, sizeof(uint32_t));

        /* save as much from the end of the filename as possible */
        size_t len = strlen(file);
        size_t available = sizeof(data.data) - sizeof(uint32_t);
        const char* file_str = file;
        if (len > available)
        {
            size_t start_idx = len - available;
            file_str = &file[start_idx];
        }
        strncpy((char*) &data.data[4], file_str, available);
        ErrorStorage_Run_Store(&data);

        _stop();
    }
}

/* Cortex-M4 core handlers */
__attribute__((used))
static void prvGetRegistersFromStack( uint32_t *pulFaultStackAddress )
{
    /* These are volatile to try and prevent the compiler/linker optimising them
    away as the variables never actually get used. If the debugger won't show the
    values of the variables, make them global by moving their declaration outside
    of this function. */
    volatile uint32_t r0;
    volatile uint32_t r1;
    volatile uint32_t r2;
    volatile uint32_t r3;
    volatile uint32_t r12;
    uint32_t lr; /* Link register. */
    uint32_t pc; /* Program counter. */
    uint32_t psr;/* Program status register. */

    r0 = pulFaultStackAddress[ 0 ];
    r1 = pulFaultStackAddress[ 1 ];
    r2 = pulFaultStackAddress[ 2 ];
    r3 = pulFaultStackAddress[ 3 ];

    r12 = pulFaultStackAddress[ 4 ];
    lr = pulFaultStackAddress[ 5 ];
    pc = pulFaultStackAddress[ 6 ];
    psr = pulFaultStackAddress[ 7 ];

    /* suppress warnings */
    (void) r0;
    (void) r1;
    (void) r2;
    (void) r3;
    (void) r12;

    uint32_t cfsr = SCB->CFSR;
    uint32_t dfsr = SCB->DFSR;
    uint32_t hfsr = SCB->HFSR;

    SEGGER_RTT_printf(0, "HardFault (%x) at %x\n", psr, pc);
    /* log the most important registers */
    ErrorInfo_t data = {
        .error_id = ERROR_ID_HARD_FAULT
    };
    memset(&data.data[0], 0u, sizeof(data.data));

    memcpy(&data.data[0], &pc, sizeof(uint32_t));
    memcpy(&data.data[4], &psr, sizeof(uint32_t));
    memcpy(&data.data[8], &lr, sizeof(uint32_t));
    memcpy(&data.data[12], &cfsr, sizeof(uint32_t));
    memcpy(&data.data[16], &dfsr, sizeof(uint32_t));
    memcpy(&data.data[20], &hfsr, sizeof(uint32_t));
    ErrorStorage_Run_Store(&data);

    _stop();
}

void NMI_Handler( void ){
    _stop();
}

__attribute__((naked))
void HardFault_Handler( void )
{
    __asm volatile
    (
        " tst lr, #4                                                \n"
        " ite eq                                                    \n"
        " mrseq r0, msp                                             \n"
        " mrsne r0, psp                                             \n"
        " ldr r1, [r0, #24]                                         \n"
        " ldr r2, handler2_address_const                            \n"
        " bx r2                                                     \n"
        " handler2_address_const: .word prvGetRegistersFromStack    \n"
    );
}
void MemManage_Handler( void )
{
    _stop();
}
void BusFault_Handler( void )
{
    _stop();
}
void UsageFault_Handler( void )
{
    _stop();
}
void SVC_Handler( void )
{
    _stop();
}
void DebugMon_Handler( void )
{
    _stop();
}

void vApplicationStackOverflowHook(TaskHandle_t xTask, char *pcTaskName)
{
    (void) xTask;

    ErrorInfo_t data = {
        .error_id = ERROR_ID_STACK_OVERFLOW
    };
    memset(&data.data[0], 0u, sizeof(data.data));

    strncpy((char*) &data.data[0], pcTaskName, sizeof(data.data));
    ErrorStorage_Run_Store(&data);

    _stop();
}

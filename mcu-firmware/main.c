#include "driver_init.h"
#include "rrrc_hal.h"
#include "rrrc_worklogic.h"
#include "error_ids.h"

#include <string.h>

static TaskHandle_t xRRRC_Main_xTask;

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

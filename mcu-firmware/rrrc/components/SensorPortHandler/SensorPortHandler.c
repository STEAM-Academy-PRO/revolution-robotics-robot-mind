#include "SensorPortHandler.h"
#include "utils.h"
#include "utils_assert.h"

/* Begin User Code Section: Declarations */

#include "SensorPortHandlerInternal.h"
#include "utils.h"
#include <string.h>
#include <hal_gpio.h>

#include "SensorPortLibraries/Dummy/Dummy.h"
#include "SensorPortLibraries/BumperSwitch/BumperSwitch.h"
#include "SensorPortLibraries/HC_SR04/HC_SR04.h"
#include "SensorPortLibraries/RGB/RGB.h"
#include "SensorPortLibraries/DebugRTC/DebugRTC.h"

#include "SEGGER_RTT.h"

static const SensorLibrary_t* libraries[] =
{
    &sensor_library_dummy,
    &sensor_library_bumper_switch,
    &sensor_library_hc_sr04,
    &sensor_library_rgb,
    &sensor_library_debug_rtc
};

static size_t sensorPortCount = 0u;
static SensorPort_t* sensorPorts = NULL;

void SensorPort_ext1_callback(void* user_data)
{
    SensorPort_t* port = (SensorPort_t*) user_data;

    if (port != NULL && port->library != NULL)
    {
        port->library->InterruptHandler(port, SensorPort_Read_Gpio1(port));
    }
}

static void _init_port(SensorPort_t* port)
{
    gpio_set_pin_pull_mode(port->comm_pin0.pin, GPIO_PULL_OFF);
    gpio_set_pin_pull_mode(port->comm_pin1.pin, GPIO_PULL_OFF);
    gpio_set_pin_function(port->comm_pin0.pin, GPIO_PIN_FUNCTION_OFF);
    gpio_set_pin_function(port->comm_pin1.pin, GPIO_PIN_FUNCTION_OFF);

    /* init led pins */
    gpio_set_pin_pull_mode(port->led0, GPIO_PULL_UP);
    gpio_set_pin_function(port->led0, GPIO_PIN_FUNCTION_OFF);
    gpio_set_pin_direction(port->led0, GPIO_DIRECTION_OUT);
    SensorPort_SetGreenLed(port, false);

    gpio_set_pin_pull_mode(port->led1, GPIO_PULL_UP);
    gpio_set_pin_function(port->led1, GPIO_PIN_FUNCTION_OFF);
    gpio_set_pin_direction(port->led1, GPIO_DIRECTION_OUT);
    SensorPort_SetOrangeLed(port, false);

    /* init vccio pin */
    gpio_set_pin_pull_mode(port->vccio, GPIO_PULL_OFF);
    gpio_set_pin_function(port->vccio, GPIO_PIN_FUNCTION_OFF);
    gpio_set_pin_direction(port->vccio, GPIO_DIRECTION_OUT);
    gpio_set_pin_level(port->vccio, false);

    SensorPort_ConfigureGpio0_Input(port);
    SensorPort_ConfigureGpio1_Input(port);

    _gpio_set_continuous_sampling(port->gpio0);

    /* set dummy library */
    port->interfaceType = SensorPortComm_None;
    port->library = &sensor_library_dummy;
    port->set_port_type_state = SetPortTypeState_None;
}

/* TODO also generate this one */
void SensorPortHandler_Run_OnInit(SensorPort_t* ports, size_t portCount)
{
    ASSERT(portCount == 4u);
    sensorPorts = ports;
    sensorPortCount = portCount;

    for (size_t i = 0u; i < portCount; i++)
    {
        _init_port(&sensorPorts[i]);
    }
}

static void OnPortDeinitCompleted(SensorPort_t* port, bool success)
{
    SEGGER_RTT_printf(0, "SensorPort %d: OnPortDeinitCompleted: %d\n", port->port_idx, success);
    if (success)
    {
        port->set_port_type_state = SetPortTypeState_DeinitDone;
    }
    else
    {
        port->set_port_type_state = SetPortTypeState_Error;
    }
}

/* End User Code Section: Declarations */

void SensorPortHandler_Run_PortUpdate(uint8_t port_idx)
{
    /* Begin User Code Section: PortUpdate:run Start */
    ASSERT(port_idx < sensorPortCount);

    SensorPort_t* port = &sensorPorts[port_idx];

    /* Do not call update if the port driver is not in a consistent state */
    if (port->set_port_type_state == SetPortTypeState_None)
    {
        port->library->UpdateAnalogData(port, SensorPortHandler_Read_AdcData(port->port_idx));
        port->library->Update(port);
    }
    /* End User Code Section: PortUpdate:run Start */
    /* Begin User Code Section: PortUpdate:run End */

    /* End User Code Section: PortUpdate:run End */
}

void SensorPortHandler_Run_ReadPortTypes(ByteArray_t* buffer)
{
    /* Begin User Code Section: ReadPortTypes:run Start */

    /* format: index (1byte), length (1byte), data (length bytes), repeating */
    uint8_t len = 0u;
    const size_t size = buffer->count;
    for (uint32_t i = 0u; i < ARRAY_SIZE(libraries); i++)
    {
        const SensorLibrary_t* lib = libraries[i];
        size_t name_length = strlen(lib->name);
        if (len + name_length + 2u > size)
        {
            buffer->count = 0u;
            return;
        }
        buffer->bytes[len] = i;
        buffer->bytes[len + 1] = name_length;
        memcpy(&buffer->bytes[len + 2], lib->name, name_length);
        len = len + 2 + name_length;
    }
    buffer->count = len;
    /* End User Code Section: ReadPortTypes:run Start */
    /* Begin User Code Section: ReadPortTypes:run End */

    /* End User Code Section: ReadPortTypes:run End */
}

void SensorPortHandler_Run_Configure(uint8_t port_idx, ByteArray_t configuration, bool* result)
{
    /* Begin User Code Section: Configure:run Start */
    if (port_idx >= sensorPortCount)
    {
        SEGGER_RTT_printf(0, "SensorPort %d: Configure Input error\n", port_idx);
        *result = false;
        return;
    }

    SensorPort_t* configuredPort = &sensorPorts[port_idx];

    if (configuredPort->library->UpdateConfiguration(configuredPort, configuration.bytes, configuration.count) == SensorLibraryStatus_Ok)
    {
        *result = true;
    }
    else
    {
        *result = false;
    }
    /* End User Code Section: Configure:run Start */
    /* Begin User Code Section: Configure:run End */

    /* End User Code Section: Configure:run End */
}

void SensorPortHandler_Run_ReadSensorInfo(uint8_t port_idx, uint8_t page, ByteArray_t* buffer)
{
    /* Begin User Code Section: ReadSensorInfo:run Start */
    if (port_idx >= sensorPortCount)
    {
        buffer->count = 0u;
        return;
    }

    SensorPort_t* port = &sensorPorts[port_idx];
    uint8_t read_count;
    port->library->ReadSensorInfo(port, page, buffer->bytes, buffer->count, &read_count);
    buffer->count = read_count;
    /* End User Code Section: ReadSensorInfo:run Start */
    /* Begin User Code Section: ReadSensorInfo:run End */

    /* End User Code Section: ReadSensorInfo:run End */
}

AsyncResult_t SensorPortHandler_AsyncRunnable_SetPortType(AsyncCommand_t asyncCommand, uint8_t port_idx, uint8_t port_type, bool* result)
{
    (void) asyncCommand;
    (void) port_idx;
    (void) port_type;
    (void) result;
    /* Begin User Code Section: SetPortType:async_run Start */
    if (port_idx >= sensorPortCount || port_type >= ARRAY_SIZE(libraries))
    {
        SEGGER_RTT_printf(0, "SensorPort %d: SetPortType(%d) Input error\n", port_idx, port_type);
        *result = false;
        return AsyncResult_Ok;
    }

    SensorPort_t *port = &sensorPorts[port_idx];
    if (asyncCommand == AsyncCommand_Start)
    {
        SEGGER_RTT_printf(0, "SensorPort %d: SetPortType(%d) Start\n", port_idx, port_type);
    }

    switch (port->set_port_type_state)
    {
        case SetPortTypeState_None:
            port->set_port_type_state = SetPortTypeState_Busy;

            port->library->DeInit(port, OnPortDeinitCompleted);
            return AsyncResult_Pending;

        case SetPortTypeState_Busy:
            port->library->DeInit(port, OnPortDeinitCompleted);
            return AsyncResult_Pending;

        case SetPortTypeState_DeinitDone:
            /* reset status slot */
            SensorPortHandler_Call_UpdatePortStatus(port->port_idx, (ByteArray_t) { NULL, 0u });
            /* set up new driver */
            port->library = libraries[port_type];
            port->library->Init(port);
            /* fall through */

        case SetPortTypeState_Done:
            SEGGER_RTT_printf(0, "SensorPort %d: SetPortType(%d) Done\n", port_idx, port_type);
            port->set_port_type_state = SetPortTypeState_None;
            *result = true;
            return AsyncResult_Ok;

        case SetPortTypeState_Error:
            SEGGER_RTT_printf(0, "SensorPort %d: SetPortType(%d) Failed\n", port_idx, port_type);
            port->set_port_type_state = SetPortTypeState_None;
            *result = false;
            return AsyncResult_Ok;

        default:
            ASSERT(0);
            return AsyncResult_Pending;
    }

    /* End User Code Section: SetPortType:async_run Start */
    /* Begin User Code Section: SetPortType:async_run End */

    /* End User Code Section: SetPortType:async_run End */
}

AsyncResult_t SensorPortHandler_AsyncRunnable_TestSensorOnPort(AsyncCommand_t asyncCommand, uint8_t port_idx, uint8_t port_type, TestSensorOnPortResult_t* result)
{
    (void) asyncCommand;
    (void) port_idx;
    (void) port_type;
    (void) result;
    /* Begin User Code Section: TestSensorOnPort:async_run Start */
    SensorOnPortStatus_t status;
    const SensorLibrary_t *lib = libraries[port_type];

    SensorPort_t *port = &sensorPorts[port_idx];
    bool test_completed = lib->TestSensorOnPort(port, &status);

    if (!test_completed)
    {
        return AsyncResult_Pending;
    }

    if (status == SensorOnPortStatus_NotPresent)
    {
        *result = TestSensorOnPortResult_NotPresent;
    }
    else if (status == SensorOnPortStatus_Present)
    {
        *result = TestSensorOnPortResult_Present;
    }
    else if (status == SensorOnPortStatus_Unknown)
    {
        *result = TestSensorOnPortResult_Unknown;
    }
    else
    {
        *result = TestSensorOnPortResult_Error;
    }

    return AsyncResult_Ok;

    /* End User Code Section: TestSensorOnPort:async_run Start */
    /* Begin User Code Section: TestSensorOnPort:async_run End */

    /* End User Code Section: TestSensorOnPort:async_run End */
}

uint8_t SensorPortHandler_Constant_PortCount(void)
{
    /* Begin User Code Section: PortCount:constant Start */

    /* End User Code Section: PortCount:constant Start */
    /* Begin User Code Section: PortCount:constant End */

    /* End User Code Section: PortCount:constant End */
    return 4;
}

__attribute__((weak))
void* SensorPortHandler_Call_Allocate(size_t size)
{
    (void) size;
    /* Begin User Code Section: Allocate:run Start */

    /* End User Code Section: Allocate:run Start */
    /* Begin User Code Section: Allocate:run End */

    /* End User Code Section: Allocate:run End */
    return NULL;
}

__attribute__((weak))
void SensorPortHandler_Call_Free(void** ptr)
{
    (void) ptr;
    /* Begin User Code Section: Free:run Start */

    /* End User Code Section: Free:run Start */
    /* Begin User Code Section: Free:run End */

    /* End User Code Section: Free:run End */
}

__attribute__((weak))
uint32_t SensorPortHandler_Call_ReadCurrentTicks(void)
{
    /* Begin User Code Section: ReadCurrentTicks:run Start */

    /* End User Code Section: ReadCurrentTicks:run Start */
    /* Begin User Code Section: ReadCurrentTicks:run End */

    /* End User Code Section: ReadCurrentTicks:run End */
    return 0u;
}

__attribute__((weak))
float SensorPortHandler_Call_ConvertTicksToMs(uint32_t ticks)
{
    (void) ticks;
    /* Begin User Code Section: ConvertTicksToMs:run Start */

    /* End User Code Section: ConvertTicksToMs:run Start */
    /* Begin User Code Section: ConvertTicksToMs:run End */

    /* End User Code Section: ConvertTicksToMs:run End */
    return 0.0f;
}

__attribute__((weak))
void SensorPortHandler_Call_UpdatePortStatus(uint8_t port, ByteArray_t data)
{
    (void) data;
    (void) port;
    /* Begin User Code Section: UpdatePortStatus:run Start */

    /* End User Code Section: UpdatePortStatus:run Start */
    /* Begin User Code Section: UpdatePortStatus:run End */

    /* End User Code Section: UpdatePortStatus:run End */
}

__attribute__((weak))
uint8_t SensorPortHandler_Read_AdcData(uint32_t index)
{
    ASSERT(index < 4);
    /* Begin User Code Section: AdcData:read Start */

    /* End User Code Section: AdcData:read Start */
    /* Begin User Code Section: AdcData:read End */

    /* End User Code Section: AdcData:read End */
    return 0u;
}

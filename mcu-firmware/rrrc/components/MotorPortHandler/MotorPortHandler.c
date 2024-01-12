#include "MotorPortHandler.h"
#include "utils.h"
#include "utils_assert.h"

/* Begin User Code Section: Declarations */
#include "MotorPortLibraries/MotorPortLibrary.h"
#include "MotorPortHandlerInternal.h"
#include "atmel_start_pins.h"
#include <string.h>

#include "MotorPortLibraries/Dummy/Dummy.h"
#include "MotorPortLibraries/DcMotor/DcMotor.h"
#include <components/MotorDriver_8833/MotorDriver_8833.h>
#include <components/ADC/ADC.h>

#include <hal_gpio.h>
#include <hal_ext_irq.h>

/*
 * In 'DETECT MOTOR' mode how many calls to TestMotorOnPort is possible to run
 * before it decides that motor is not attached
 */
#define TEST_MOTOR_ON_PORT_TIMEOUT 100

static const MotorLibrary_t* libraries[] =
{
    &motor_library_dummy,
    &motor_library_dc
};

static size_t motorPortCount = 0u;
static MotorPort_t* motorPorts = NULL;

static void _init_port(MotorPort_t* port)
{
    MotorPortHandler_Read_PortConfig(port->port_idx, &port->gpio);

    /* init led pins */
    gpio_set_pin_pull_mode(port->gpio.led, GPIO_PULL_UP);
    gpio_set_pin_function(port->gpio.led, GPIO_PIN_FUNCTION_OFF);
    gpio_set_pin_direction(port->gpio.led, GPIO_DIRECTION_OUT);
    MotorPort_SetGreenLed(port, false);

    /* encoders */
    gpio_set_pin_direction(GPIO_FROM_FAST_PIN(port->gpio.enc0), GPIO_DIRECTION_IN);
    gpio_set_pin_function(GPIO_FROM_FAST_PIN(port->gpio.enc0), GPIO_PIN_FUNCTION_A);
    gpio_set_pin_pull_mode(GPIO_FROM_FAST_PIN(port->gpio.enc0), GPIO_PULL_OFF);

    gpio_set_pin_direction(GPIO_FROM_FAST_PIN(port->gpio.enc1), GPIO_DIRECTION_IN);
    gpio_set_pin_function(GPIO_FROM_FAST_PIN(port->gpio.enc1), GPIO_PIN_FUNCTION_A);
    gpio_set_pin_pull_mode(GPIO_FROM_FAST_PIN(port->gpio.enc1), GPIO_PULL_OFF);

    __disable_irq();

    _gpio_set_continuous_sampling(GPIO_FROM_FAST_PIN(port->gpio.enc0));
    _gpio_set_continuous_sampling(GPIO_FROM_FAST_PIN(port->gpio.enc1));

    MotorPort_DisableExti0(port);
    MotorPort_DisableExti1(port);

    MotorPort_WriteMaxCurrent(port, 0.0f);

    /* set dummy library */
    port->library = &motor_library_dummy;

    __enable_irq();
}

void MotorPortHandler_Run_OnInit(MotorPort_t* ports, uint8_t portCount)
{
    motorPorts = ports;
    motorPortCount = portCount;

    MotorPortHandler_Write_PortCount(portCount);

    for (size_t i = 0u; i < portCount; i++)
    {
        _init_port(&motorPorts[i]);
    }
}
/* End User Code Section: Declarations */

void MotorPortHandler_Run_PortUpdate(uint8_t port_idx)
{
    /* Begin User Code Section: PortUpdate:run Start */
    ASSERT(port_idx < motorPortCount);

    MotorPort_t* port = &motorPorts[port_idx];
    const MotorLibrary_t* library = (const MotorLibrary_t*) port->library;
    library->Update(port);
    /* End User Code Section: PortUpdate:run Start */
    /* Begin User Code Section: PortUpdate:run End */

    /* End User Code Section: PortUpdate:run End */
}

void MotorPortHandler_Run_ReadPortTypes(ByteArray_t* buffer)
{
    /* Begin User Code Section: ReadPortTypes:run Start */

    /* format: index (1byte), length (1byte), data (length bytes), repeating */
    uint8_t len = 0u;
    const size_t size = buffer->count;
    for (uint32_t i = 0u; i < ARRAY_SIZE(libraries); i++)
    {
        const MotorLibrary_t* lib = libraries[i];
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

void MotorPortHandler_Run_SetPortType(uint8_t port_idx, uint8_t port_type, bool* result)
{
    /* Begin User Code Section: SetPortType:run Start */
    if (port_idx >= motorPortCount)
    {
        *result = false;
        return;
    }
    if (port_type >= ARRAY_SIZE(libraries))
    {
        *result = false;
        return;
    }

    MotorPort_t* configuredPort = &motorPorts[port_idx];
    const MotorLibrary_t* library = (const MotorLibrary_t*) configuredPort->library;

    library->DeInit(configuredPort);
    library = libraries[port_type];
    configuredPort->library = library;

    /* reset status slot */
    MotorPortHandler_Call_UpdatePortStatus(configuredPort->port_idx, (ByteArray_t){NULL, 0u});

    library->Init(configuredPort);
    *result = true;
    /* End User Code Section: SetPortType:run Start */
    /* Begin User Code Section: SetPortType:run End */

    /* End User Code Section: SetPortType:run End */
}

void MotorPortHandler_Run_Configure(uint8_t port_idx, ByteArray_t configuration, bool* result)
{
    /* Begin User Code Section: Configure:run Start */
    if (port_idx >= motorPortCount)
    {
        *result = false;
        return;
    }

    MotorPort_t* configuredPort = &motorPorts[port_idx];
    const MotorLibrary_t* library = (const MotorLibrary_t*) configuredPort->library;

    if (library->UpdateConfiguration(configuredPort, configuration.bytes, configuration.count) == MotorLibraryStatus_Ok)
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

bool MotorPortHandler_Run_CreateDriveRequest(uint8_t port_idx, ConstByteArray_t buffer, DriveRequest_t* request)
{
    /* Begin User Code Section: CreateDriveRequest:run Start */
    MotorPort_t* port = &motorPorts[port_idx];
    const MotorLibrary_t* library = (const MotorLibrary_t*) port->library;

    if (library->CreateDriveRequest(port, buffer.bytes, buffer.count, request) == MotorLibraryStatus_Ok)
    {
        return true;
    }
    else
    {
        return false;
    }
    /* End User Code Section: CreateDriveRequest:run Start */
    /* Begin User Code Section: CreateDriveRequest:run End */

    /* End User Code Section: CreateDriveRequest:run End */
}

extern Current_t MotorCurrentFilter_FilteredCurrent_array[6];
extern int16_t MotorPortHandler_DriveStrength_array[6];
#define TEST_MOTOR_ON_PORT_STATE_IDLING 0
#define TEST_MOTOR_ON_PORT_STATE_IN_PROGRESS 1

/*
 * This defines raw ADC value, taken from motor driver current sensing pin,
 * anything below this value is considered noise. ADC results above this value
 * speak about actual current, drawn by motor under test load. Read full
 * description of how motor on port validation is performed
 */
#define TEST_MOTOR_ON_PORT_RAW_ADC_THRESHOLD 10

static int test_motor_on_port_state = TEST_MOTOR_ON_PORT_STATE_IDLING;
static int test_motor_on_port_counter = 0;

/*
 * Knowning motor port index, tell what motor driver serves this motor and
 * on what channel. Current hardware solution uses 3 motor drivers, each
 * having 2 separate channels (A and B), each channel in turn having
 * 2 PWM-channels and 1 current sensing pin.
 */
static void MotorPortHandler_GetMotorDriverChannel(int port_idx,
    int *motor_driver_idx, int *motor_driver_channel)
{
  MotorDriver_8833_GetMotorPortDriver(port_idx, motor_driver_idx,
      motor_driver_channel);
}

/*
 * Set up ADC for successful test load currents detection:
 * - Tracking of maximum ADC value on channel should be reset to 0, to make new
 *   maximum values relevant to the upcoming test load
 *
 * - Limit ADC module to single continuos channel sampling in order to detect
 *   small test-load currents drawn by motor.
 *
 *   In normal mode ADC component reads many channels in sequentual order and
 *   looses small motor currents due to sparse sampling time. Same small test
 *   load currents are detected successfully if ADC component samples one ADC
 *   channel all the time.
 */

#define PORT_IDX_FW_INVALID -1

static int PortIndexAppToFw(int port_idx_app)
{
  /* Application port indices here are in to 0-based */
  const int app_to_fw_port_idx_map[] = { 5, 4, 3, 0, 1, 2 };
  if ((unsigned)port_idx_app >= ARRAY_SIZE(app_to_fw_port_idx_map))
  {
    return PORT_IDX_FW_INVALID;
  }
  return app_to_fw_port_idx_map[port_idx_app];
}

AsyncResult_t MotorPortHandler_AsyncRunnable_TestMotorOnPort(AsyncCommand_t asyncCommand, uint8_t port_idx, uint8_t test_power, uint8_t threshold, bool* result)
{
    (void) asyncCommand;

    /* Begin User Code Section: TestMotorOnPort:async_run Start */
    int motor_driver_index;
    int motor_driver_channel;
    int port_idx_fw;
    bool valid_request = true;

    bool motor_detected = false;

    port_idx_fw = PortIndexAppToFw(port_idx);
    valid_request = port_idx_fw != PORT_IDX_FW_INVALID;

    if (valid_request)
    {
        MotorPortHandler_GetMotorDriverChannel(port_idx_fw, &motor_driver_index,
            &motor_driver_channel);
    }

    if (test_motor_on_port_state == TEST_MOTOR_ON_PORT_STATE_IDLING)
    {
        if (!valid_request)
        {
            *result = false;
            return AsyncResult_Ok;
        }

        MotorDriver_8833_TestLoadStart(motor_driver_index, motor_driver_channel,
            test_power);

        if (!ADC_DetectMotorStart(port_idx_fw, threshold))
        {
            *result = false;
            MotorDriver_8833_TestLoadStop(motor_driver_index, motor_driver_channel);
            return AsyncResult_Ok;
        }

        test_motor_on_port_counter = TEST_MOTOR_ON_PORT_TIMEOUT;
        test_motor_on_port_state = TEST_MOTOR_ON_PORT_STATE_IN_PROGRESS;

        return AsyncResult_Pending;
    }

    if (test_motor_on_port_state == TEST_MOTOR_ON_PORT_STATE_IN_PROGRESS)
    {
        if (ADC_DetectMotorDetected())
        {
            motor_detected = true;
        }
        else if (!valid_request)
        {
            /*
             * in case of request not passing validity check we return false
             * for now, but TODO: need to implement more states
             */
            motor_detected = false;
        }
        else
        {
            test_motor_on_port_counter--;
            if (test_motor_on_port_counter)
            {
                return AsyncResult_Pending;
            }
            ADC_DetectMotorStop();
        }
    }

    MotorDriver_8833_TestLoadStop(motor_driver_index, motor_driver_channel);
    test_motor_on_port_state = TEST_MOTOR_ON_PORT_STATE_IDLING;

    *result = motor_detected;
    return AsyncResult_Ok;

    /* End User Code Section: TestMotorOnPort:async_run Start */
    /* Begin User Code Section: TestMotorOnPort:async_run End */

    /* End User Code Section: TestMotorOnPort:async_run End */
}

__attribute__((weak))
void* MotorPortHandler_Call_Allocate(size_t size)
{
    (void) size;
    /* Begin User Code Section: Allocate:run Start */

    /* End User Code Section: Allocate:run Start */
    /* Begin User Code Section: Allocate:run End */

    /* End User Code Section: Allocate:run End */
    return NULL;
}

__attribute__((weak))
void MotorPortHandler_Call_Free(void** ptr)
{
    (void) ptr;
    /* Begin User Code Section: Free:run Start */

    /* End User Code Section: Free:run Start */
    /* Begin User Code Section: Free:run End */

    /* End User Code Section: Free:run End */
}

__attribute__((weak))
void MotorPortHandler_Call_UpdatePortStatus(uint8_t port, ByteArray_t data)
{
    (void) data;
    (void) port;
    /* Begin User Code Section: UpdatePortStatus:run Start */

    /* End User Code Section: UpdatePortStatus:run Start */
    /* Begin User Code Section: UpdatePortStatus:run End */

    /* End User Code Section: UpdatePortStatus:run End */
}

__attribute__((weak))
void MotorPortHandler_Write_DriveStrength(uint32_t index, int16_t value)
{
    (void) value;
    ASSERT(index < 6);
    /* Begin User Code Section: DriveStrength:write Start */

    /* End User Code Section: DriveStrength:write Start */
    /* Begin User Code Section: DriveStrength:write End */

    /* End User Code Section: DriveStrength:write End */
}

__attribute__((weak))
void MotorPortHandler_Write_MaxAllowedCurrent(uint32_t index, Current_t value)
{
    (void) value;
    ASSERT(index < 6);
    /* Begin User Code Section: MaxAllowedCurrent:write Start */

    /* End User Code Section: MaxAllowedCurrent:write Start */
    /* Begin User Code Section: MaxAllowedCurrent:write End */

    /* End User Code Section: MaxAllowedCurrent:write End */
}

__attribute__((weak))
void MotorPortHandler_Write_PortCount(uint8_t value)
{
    (void) value;
    /* Begin User Code Section: PortCount:write Start */

    /* End User Code Section: PortCount:write Start */
    /* Begin User Code Section: PortCount:write End */

    /* End User Code Section: PortCount:write End */
}

__attribute__((weak))
void MotorPortHandler_Read_DriveRequest(uint32_t index, DriveRequest_t* value)
{
    ASSERT(index < 6);
    ASSERT(value != NULL);
    /* Begin User Code Section: DriveRequest:read Start */

    /* End User Code Section: DriveRequest:read Start */
    *value = (DriveRequest_t) {
        .version      = 0u,
        .power_limit  = 0.0f,
        .speed_limit  = 0.0f,
        .request_type = DriveRequest_RequestType_Power,
        .request      = {
            .power = 0
        }
    };
    /* Begin User Code Section: DriveRequest:read End */

    /* End User Code Section: DriveRequest:read End */
}

__attribute__((weak))
void MotorPortHandler_Read_PortConfig(uint32_t index, MotorPortGpios_t* value)
{
    ASSERT(index < 6);
    ASSERT(value != NULL);
    /* Begin User Code Section: PortConfig:read Start */

    /* End User Code Section: PortConfig:read Start */
    *value = (MotorPortGpios_t) {
        .led  = 0u,
        .enc0 = {0},
        .enc1 = {0}
    };
    /* Begin User Code Section: PortConfig:read End */

    /* End User Code Section: PortConfig:read End */
}

__attribute__((weak))
Percentage_t MotorPortHandler_Read_RelativeMotorCurrent(uint32_t index)
{
    ASSERT(index < 6);
    /* Begin User Code Section: RelativeMotorCurrent:read Start */

    /* End User Code Section: RelativeMotorCurrent:read Start */
    /* Begin User Code Section: RelativeMotorCurrent:read End */

    /* End User Code Section: RelativeMotorCurrent:read End */
    return (Percentage_t) 100.0f;
}

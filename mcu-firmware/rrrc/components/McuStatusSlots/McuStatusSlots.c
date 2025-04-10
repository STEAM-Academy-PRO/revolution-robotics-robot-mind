#include "McuStatusSlots.h"
#include "utils.h"
#include "utils_assert.h"

/* Begin User Code Section: Declarations */
#include <math.h>
#include <string.h>

#define SENSOR_PORT_COUNT   ((size_t) 4u)
#define MOTOR_PORT_COUNT    ((size_t) 6u)

#define STATUS_SLOT_BATTERY ((uint8_t) 10u)
#define STATUS_SLOT_AXL     ((uint8_t) 11u)
#define STATUS_SLOT_GYRO    ((uint8_t) 12u)
#define STATUS_SLOT_RESET   ((uint8_t) 13u)
#define STATUS_SLOT_ORIENTATION ((uint8_t) 14u)

typedef struct {
    /** The buffer that hold the data. The buffer may be bigger than the actual data in it. */
    ByteArray_t buffer;
    /** The actual number of bytes in the buffer. */
    uint8_t size;
    /** An ID that is used to detect if the value has changed. Incremented on write. */
    uint8_t version;
} slot_t;

#define MOTOR_SLOT(x)  (x)
#define SENSOR_SLOT(x) (x + MOTOR_PORT_COUNT)

static uint8_t battery_status[4];
static uint8_t axl_status[6];
static uint8_t gyro_status[6];
static uint8_t reset_status[1];
static uint8_t orientation_status[12];

static slot_t slots[16] = {
    { .buffer = { .bytes = NULL,               .count = 0u,                             }, .size = 0u, .version = 0u },
    { .buffer = { .bytes = NULL,               .count = 0u,                             }, .size = 0u, .version = 0u },
    { .buffer = { .bytes = NULL,               .count = 0u,                             }, .size = 0u, .version = 0u },
    { .buffer = { .bytes = NULL,               .count = 0u,                             }, .size = 0u, .version = 0u },
    { .buffer = { .bytes = NULL,               .count = 0u,                             }, .size = 0u, .version = 0u },
    { .buffer = { .bytes = NULL,               .count = 0u,                             }, .size = 0u, .version = 0u },
    { .buffer = { .bytes = NULL,               .count = 0u,                             }, .size = 0u, .version = 0u },
    { .buffer = { .bytes = NULL,               .count = 0u,                             }, .size = 0u, .version = 0u },
    { .buffer = { .bytes = NULL,               .count = 0u,                             }, .size = 0u, .version = 0u },
    { .buffer = { .bytes = NULL,               .count = 0u,                             }, .size = 0u, .version = 0u },
    { .buffer = { .bytes = battery_status,     .count = ARRAY_SIZE(battery_status),     }, .size = 0u, .version = 0u },
    { .buffer = { .bytes = axl_status,         .count = ARRAY_SIZE(axl_status),         }, .size = 0u, .version = 0u },
    { .buffer = { .bytes = gyro_status,        .count = ARRAY_SIZE(gyro_status),        }, .size = 0u, .version = 0u },
    { .buffer = { .bytes = reset_status,       .count = ARRAY_SIZE(reset_status),       }, .size = 0u, .version = 0u },
    { .buffer = { .bytes = orientation_status, .count = ARRAY_SIZE(orientation_status), }, .size = 0u, .version = 0u }
};

static bool compare_and_copy(uint8_t* pDst, const uint8_t* pSrc, size_t size)
{
    bool equal = true;
    for (uint8_t i = 0u; i < size; i++)
    {
        if (pSrc[i] != pDst[i])
        {
            pDst[i] = pSrc[i];
            equal = false;
        }
    }

    return equal;
}

static bool slot_has_data(const slot_t* slot)
{
    return ((slot->version & 0x80u) == 0u);
}

static void update_slot(uint8_t index, const uint8_t* data, uint8_t data_size)
{
    slot_t* const slot = &slots[index];
    ASSERT(data_size <= slot->buffer.count);

    bool slot_changed = true;
    uint32_t primask = __get_PRIMASK();
    __disable_irq();
    if (slot_has_data(slot) && data_size == slot->size)
    {
        slot_changed = !compare_and_copy(slot->buffer.bytes, data, slot->size);
    }
    else
    {
        memcpy(slot->buffer.bytes, data, data_size);
        slot->size = data_size;
    }

    if (slot_changed)
    {
        slot->version = (slot->version + 1u) & 0x7Fu;
        McuStatusSlots_Write_SlotData(index, (const SlotData_t) {
            .data = (ByteArray_t) {
                .bytes = slot->buffer.bytes,
                .count = slot->size
            },
            .version = slot->version
        });
    }
    __set_PRIMASK(primask);
}

static void _realloc_slot(slot_t* slot, size_t size)
{
    if (size > slot->buffer.count)
    {
        if (slot->buffer.bytes != NULL)
        {
            McuStatusSlots_Call_Free((void**) &slot->buffer.bytes);
        }

        uint8_t* new_buffer = (uint8_t*) McuStatusSlots_Call_Allocate(size);
        ASSERT (new_buffer != NULL);

        slot->buffer.bytes = new_buffer;
        slot->buffer.count = size;
    }

    /* Clear slot data */
    slot->size = 0u;
    slot->version = 0xFFu;
}
/* End User Code Section: Declarations */

void McuStatusSlots_Run_Reset(void)
{
    /* Begin User Code Section: Reset:run Start */
    uint32_t primask = __get_PRIMASK();
    __disable_irq();
    for (size_t i = 0u; i < ARRAY_SIZE(slots); i++)
    {
        slots[i].size = 0u;
        slots[i].version = 0xFFu;
    }
    __set_PRIMASK(primask);

    uint8_t reset_data = 0x5Au;
    update_slot(STATUS_SLOT_RESET, &reset_data, 1u);
    /* End User Code Section: Reset:run Start */
    /* Begin User Code Section: Reset:run End */

    /* End User Code Section: Reset:run End */
}

void McuStatusSlots_Run_Update(void)
{
    /* Begin User Code Section: Update:run Start */

    /* battery slot */
    {
        const uint8_t status[4] = {
            (uint8_t) McuStatusSlots_Read_MainBatteryStatus(),
            McuStatusSlots_Read_MainBatteryLevel(),
            McuStatusSlots_Read_MotorBatteryPresent(),
            McuStatusSlots_Read_MotorBatteryLevel()
        };

        update_slot(STATUS_SLOT_BATTERY, status, sizeof(status));
    }
    /* IMU slots */
    // TODO Use processed/filtered values instead of raw
    {
        IMU_RawSample_t sample;
        McuStatusSlots_Read_Acceleration(&sample);

        update_slot(STATUS_SLOT_AXL, (const uint8_t*) &sample, sizeof(sample));
    }
    {
        IMU_RawSample_t sample;
        McuStatusSlots_Read_AngularSpeeds(&sample);

        update_slot(STATUS_SLOT_GYRO, (const uint8_t*) &sample, sizeof(sample));
    }
    {
        Orientation3D_t sample;
        McuStatusSlots_Read_Orientation(&sample);

        update_slot(STATUS_SLOT_ORIENTATION, (const uint8_t*) &sample, sizeof(sample));
    }

    /* End User Code Section: Update:run Start */
    /* Begin User Code Section: Update:run End */

    /* End User Code Section: Update:run End */
}

void McuStatusSlots_Run_ChangeSensorPortSlotSize(size_t size)
{
    /* Begin User Code Section: ChangeSensorPortSlotSize:run Start */
    for (size_t i = 0u; i < SENSOR_PORT_COUNT; i++)
    {
        _realloc_slot(&slots[SENSOR_SLOT(i)], size);
    }
    /* End User Code Section: ChangeSensorPortSlotSize:run Start */
    /* Begin User Code Section: ChangeSensorPortSlotSize:run End */

    /* End User Code Section: ChangeSensorPortSlotSize:run End */
}

void McuStatusSlots_Run_ChangeMotorPortSlotSize(size_t size)
{
    /* Begin User Code Section: ChangeMotorPortSlotSize:run Start */
    for (size_t i = 0u; i < MOTOR_PORT_COUNT; i++)
    {
        _realloc_slot(&slots[MOTOR_SLOT(i)], size);
    }
    /* End User Code Section: ChangeMotorPortSlotSize:run Start */
    /* Begin User Code Section: ChangeMotorPortSlotSize:run End */

    /* End User Code Section: ChangeMotorPortSlotSize:run End */
}

void McuStatusSlots_Run_UpdateSensorPort(uint8_t port, ByteArray_t data)
{
    /* Begin User Code Section: UpdateSensorPort:run Start */
    update_slot(SENSOR_SLOT(port), data.bytes, data.count);
    /* End User Code Section: UpdateSensorPort:run Start */
    /* Begin User Code Section: UpdateSensorPort:run End */

    /* End User Code Section: UpdateSensorPort:run End */
}

void McuStatusSlots_Run_UpdateMotorPort(uint8_t port, ByteArray_t data)
{
    /* Begin User Code Section: UpdateMotorPort:run Start */
    update_slot(MOTOR_SLOT(port), data.bytes, data.count);
    /* End User Code Section: UpdateMotorPort:run Start */
    /* Begin User Code Section: UpdateMotorPort:run End */

    /* End User Code Section: UpdateMotorPort:run End */
}

__attribute__((weak))
void* McuStatusSlots_Call_Allocate(size_t size)
{
    (void) size;
    /* Begin User Code Section: Allocate:run Start */

    /* End User Code Section: Allocate:run Start */
    /* Begin User Code Section: Allocate:run End */

    /* End User Code Section: Allocate:run End */
    return NULL;
}

__attribute__((weak))
void McuStatusSlots_Call_Free(void** ptr)
{
    (void) ptr;
    /* Begin User Code Section: Free:run Start */

    /* End User Code Section: Free:run Start */
    /* Begin User Code Section: Free:run End */

    /* End User Code Section: Free:run End */
}

__attribute__((weak))
void McuStatusSlots_Write_SlotData(uint32_t index, SlotData_t value)
{
    (void) value;
    ASSERT(index < 16);
    /* Begin User Code Section: SlotData:write Start */

    /* End User Code Section: SlotData:write Start */
    /* Begin User Code Section: SlotData:write End */

    /* End User Code Section: SlotData:write End */
}

__attribute__((weak))
void McuStatusSlots_Read_Acceleration(IMU_RawSample_t* value)
{
    ASSERT(value != NULL);
    /* Begin User Code Section: Acceleration:read Start */

    /* End User Code Section: Acceleration:read Start */
    *value = (IMU_RawSample_t) {
        .x = 0,
        .y = 0,
        .z = 0
    };
    /* Begin User Code Section: Acceleration:read End */

    /* End User Code Section: Acceleration:read End */
}

__attribute__((weak))
void McuStatusSlots_Read_AngularSpeeds(IMU_RawSample_t* value)
{
    ASSERT(value != NULL);
    /* Begin User Code Section: AngularSpeeds:read Start */

    /* End User Code Section: AngularSpeeds:read Start */
    *value = (IMU_RawSample_t) {
        .x = 0,
        .y = 0,
        .z = 0
    };
    /* Begin User Code Section: AngularSpeeds:read End */

    /* End User Code Section: AngularSpeeds:read End */
}

__attribute__((weak))
uint8_t McuStatusSlots_Read_MainBatteryLevel(void)
{
    /* Begin User Code Section: MainBatteryLevel:read Start */

    /* End User Code Section: MainBatteryLevel:read Start */
    /* Begin User Code Section: MainBatteryLevel:read End */

    /* End User Code Section: MainBatteryLevel:read End */
    return 0u;
}

__attribute__((weak))
ChargerState_t McuStatusSlots_Read_MainBatteryStatus(void)
{
    /* Begin User Code Section: MainBatteryStatus:read Start */

    /* End User Code Section: MainBatteryStatus:read Start */
    /* Begin User Code Section: MainBatteryStatus:read End */

    /* End User Code Section: MainBatteryStatus:read End */
    return ChargerState_NotPluggedIn;
}

__attribute__((weak))
uint8_t McuStatusSlots_Read_MotorBatteryLevel(void)
{
    /* Begin User Code Section: MotorBatteryLevel:read Start */

    /* End User Code Section: MotorBatteryLevel:read Start */
    /* Begin User Code Section: MotorBatteryLevel:read End */

    /* End User Code Section: MotorBatteryLevel:read End */
    return 0u;
}

__attribute__((weak))
bool McuStatusSlots_Read_MotorBatteryPresent(void)
{
    /* Begin User Code Section: MotorBatteryPresent:read Start */

    /* End User Code Section: MotorBatteryPresent:read Start */
    /* Begin User Code Section: MotorBatteryPresent:read End */

    /* End User Code Section: MotorBatteryPresent:read End */
    return false;
}

__attribute__((weak))
void McuStatusSlots_Read_Orientation(Orientation3D_t* value)
{
    ASSERT(value != NULL);
    /* Begin User Code Section: Orientation:read Start */

    /* End User Code Section: Orientation:read Start */
    *value = (Orientation3D_t) {
        .pitch = 0.0f,
        .roll  = 0.0f,
        .yaw   = 0.0f
    };
    /* Begin User Code Section: Orientation:read End */

    /* End User Code Section: Orientation:read End */
}

__attribute__((weak))
float McuStatusSlots_Read_YawAngle(void)
{
    /* Begin User Code Section: YawAngle:read Start */

    /* End User Code Section: YawAngle:read Start */
    /* Begin User Code Section: YawAngle:read End */

    /* End User Code Section: YawAngle:read End */
    return 0.0f;
}

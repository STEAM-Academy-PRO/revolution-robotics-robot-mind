#include "LedDisplayController.h"
#include "utils.h"
#include "utils_assert.h"

/* Begin User Code Section: Declarations */
#include "CommonLibraries/functions.h"
#include <math.h>

#define MAIN_BATTERY_INDICATOR_LED  0
#define MOTOR_BATTERY_INDICATOR_LED 1
#define BLUETOOTH_INDICATOR_LED     2
#define STATUS_INDICATOR_LED        3

#define BLUETOOTH_BLINK_PERIOD    121
#define BLUETOOTH_BLINK_LENGTH     5

#define CHARGING_BLINK_PERIOD    120
#define CHARGING_BLINK_LENGTH     10

#define MOTOR_MISSING_BLINK_PERIOD    50
#define MOTOR_MISSING_BLINK_LENGTH    30

#define BLE_ON_COLOR                (rgb_t) LED_CYAN
#define BLE_OFF_COLOR               (rgb_t) LED_OFF
#define BLE_NOT_INITIALIZED_COLOR   (rgb_t) LED_OFF

#define MASTER_UNKNOWN_COLOR        (rgb_t) LED_OFF
#define MASTER_NOT_CONFIGURED_COLOR (rgb_t) LED_RED
#define MASTER_OPERATIONAL_COLOR    (rgb_t) LED_ORANGE
#define MASTER_CONTROLLED_COLOR     (rgb_t) LED_GREEN
#define MASTER_CONFIGURING_COLOR    (rgb_t) LED_CYAN
#define MASTER_UPDATING_COLOR       (rgb_t) LED_RED

typedef enum {
    LedDisplayMode_SwitchedOff,
    LedDisplayMode_LowBattery,
    LedDisplayMode_Normal,
} LedDisplayMode_t;

static uint32_t _motor_battery_feedback;
static LedDisplayMode_t _previous_display_mode;
static uint32_t _charging_blink_timer;
static uint32_t _ble_blink_timer;
static uint32_t _motor_blink_timer;
static bool _motor_battery_blinking;

/**
 * Returns whether any of the motors are active
 */
static bool _motors_active(void)
{
    for (uint32_t i = 0u; i < 6u; i++)
    {
        if (LedDisplayController_Read_MotorDriveValues(i) != 0)
        {
            return true;
        }
    }
    return false;
}

/**
 * Based on a counter value and two timing parameters,
 * return true if a blinking LED should be ON and false if it should be OFF.
 *
 * @param on_time uint32_t The amount of time the LED should be ON
 * @param period uint32_t The amount of time between two blinks (from start to start)
 * @return bool if the LED should be turned ON
 */
static bool _blink(uint32_t* timer, uint32_t on_time, uint32_t period)
{
    if (*timer < on_time)
    {
        (*timer)++;
        return true;
    }
    else if (*timer < period)
    {
        (*timer)++;
        return false;
    }
    else
    {
        *timer = 0u;
        return false;
    }
}

static void _clear_display(void)
{
    for (uint32_t i = 0u; i < 4u; i++)
    {
        LedDisplayController_Write_StatusLeds(i, (rgb_t) LED_OFF);
    }
    for (uint32_t i = 0u; i < 12u; i++)
    {
        LedDisplayController_Write_RingLeds(i, (rgb_t) LED_OFF);
    }
}

static LedDisplayMode_t _get_display_mode(void)
{
    if (!LedDisplayController_Read_MainBatteryDetected())
    {
        // Assume charging-while-off. This is a hack because we can't reliable observe
        // the power switch state across hardware versions. However, on old hardware (PCB v1)
        // we can't charge while off, and on new hardware (PCB v3) we can't measure the battery
        // while off. So this is a safe assumption.
        return LedDisplayMode_SwitchedOff;
    }

    if (LedDisplayController_Read_MainBatteryLow())
    {
        return LedDisplayMode_LowBattery;
    }

    return LedDisplayMode_Normal;
}

static rgb_t _display_main_battery(void)
{
    switch (LedDisplayController_Read_MainBatteryStatus())
    {
        case ChargerState_NotPluggedIn:
        case ChargerState_Charged:
            break;

        case ChargerState_Charging:
            if (_blink(&_charging_blink_timer, CHARGING_BLINK_LENGTH, CHARGING_BLINK_PERIOD))
            {
                return (rgb_t) LED_BLUE;
            }
            break;

        case ChargerState_Fault:
            if (_blink(&_charging_blink_timer, CHARGING_BLINK_LENGTH, CHARGING_BLINK_PERIOD))
            {
                return (rgb_t) LED_RED;
            }
            else
            {
                return (rgb_t) LED_OFF;
            }
            break;
    }

    rgb_t color;

    uint8_t percentage = LedDisplayController_Read_MainBatteryLevel();
    color.G = lroundf(map_constrained(percentage, 10, 90, 0, LED_BRIGHT));
    color.R = lroundf(map_constrained(percentage, 20, 60, LED_BRIGHT, 0));
    color.B = 0u;

    return color;
}

static rgb_t _display_main_battery_while_off(void)
{
    switch (LedDisplayController_Read_MainBatteryStatus())
    {
        case ChargerState_Charged:
            return (rgb_t) LED_GREEN;

        case ChargerState_Charging:
            if (_blink(&_charging_blink_timer, CHARGING_BLINK_LENGTH, CHARGING_BLINK_PERIOD))
            {
                return (rgb_t) LED_BLUE;
            }
            else
            {
                return (rgb_t) LED_OFF;
            }

        case ChargerState_Fault:
            if (_blink(&_charging_blink_timer, CHARGING_BLINK_LENGTH, CHARGING_BLINK_PERIOD))
            {
                return (rgb_t) LED_RED;
            }
            else
            {
                return (rgb_t) LED_OFF;
            }

        default:
        case ChargerState_NotPluggedIn:
            // This is impossible, something powers the board. Indicate charging.
            return (rgb_t) LED_BLUE;
    }
}

static rgb_t _display_motor_battery(void)
{
    bool battery_present = LedDisplayController_Read_MotorBatteryPresent();
    bool motor_battery_should_blink = _motors_active() && !battery_present;

    if (motor_battery_should_blink && !_motor_battery_blinking)
    {
        _motor_battery_blinking = true;
        _motor_blink_timer = 0u;
    }

    if (_motor_battery_blinking)
    {
        bool blink = _blink(&_motor_blink_timer, MOTOR_MISSING_BLINK_LENGTH, MOTOR_MISSING_BLINK_PERIOD);
        if (!motor_battery_should_blink && _motor_blink_timer == 0u)
        {
            _motor_battery_blinking = false;
        }

        if (blink)
        {
            return (rgb_t) LED_RED;
        }
        else
        {
            return (rgb_t) LED_OFF;
        }
    }

    if (!battery_present)
    {
        return (rgb_t) LED_OFF;
    }

    rgb_t color;

    uint8_t percentage = LedDisplayController_Read_MotorBatteryLevel();
    color.G = lroundf(map_constrained(percentage, 10, 90, 0, LED_BRIGHT));
    color.R = lroundf(map_constrained(percentage, 50, 90, LED_BRIGHT, 0));
    color.B = 0u;

    return color;
}
/* End User Code Section: Declarations */

void LedDisplayController_Run_OnInit(void)
{
    /* Begin User Code Section: OnInit:run Start */
    _motor_battery_feedback = 0u;
    _previous_display_mode = LedDisplayMode_Normal;

    _charging_blink_timer = 0u;
    _ble_blink_timer = 0u;
    _motor_blink_timer = 0u;

    _motor_battery_blinking = false;

    LedDisplayController_Write_MaxBrightness(LedDisplayController_Read_DefaultBrightness());
    /* End User Code Section: OnInit:run Start */
    /* Begin User Code Section: OnInit:run End */

    /* End User Code Section: OnInit:run End */
}

void LedDisplayController_Run_Update(void)
{
    /* Begin User Code Section: Update:run Start */
    LedDisplayMode_t current_display_mode = _get_display_mode();

    if (current_display_mode != _previous_display_mode)
    {
        _clear_display();
        switch (current_display_mode)
        {
            default:
                break;

            case LedDisplayMode_SwitchedOff:
                LedDisplayController_Write_MaxBrightness(LedDisplayController_Read_PowerOffBrightness());
                break;

            case LedDisplayMode_LowBattery:
                LedDisplayController_Write_MaxBrightness(LedDisplayController_Read_LowBatteryBrightness());
                break;

            case LedDisplayMode_Normal:
                LedDisplayController_Write_MaxBrightness(LedDisplayController_Read_DefaultBrightness());
                break;
        }
    }

    switch (current_display_mode)
    {
        case LedDisplayMode_Normal:
            LedDisplayController_Write_StatusLeds(MAIN_BATTERY_INDICATOR_LED, _display_main_battery());
            LedDisplayController_Write_StatusLeds(MOTOR_BATTERY_INDICATOR_LED, _display_motor_battery());

            switch (LedDisplayController_Read_BluetoothStatus())
            {
                case BluetoothStatus_Inactive:
                    LedDisplayController_Write_StatusLeds(BLUETOOTH_INDICATOR_LED, BLE_NOT_INITIALIZED_COLOR);
                    _ble_blink_timer = 0u;
                    break;

                case BluetoothStatus_NotConnected:
                    if (_blink(&_ble_blink_timer, BLUETOOTH_BLINK_LENGTH, BLUETOOTH_BLINK_PERIOD))
                    {
                        LedDisplayController_Write_StatusLeds(BLUETOOTH_INDICATOR_LED, BLE_ON_COLOR);
                    }
                    else
                    {
                        LedDisplayController_Write_StatusLeds(BLUETOOTH_INDICATOR_LED, BLE_OFF_COLOR);
                    }
                    break;

                case BluetoothStatus_Connected:
                    LedDisplayController_Write_StatusLeds(BLUETOOTH_INDICATOR_LED, BLE_ON_COLOR);
                    _ble_blink_timer = 0u;
                    break;
            }

            switch (LedDisplayController_Read_MasterStatus())
            {
                case MasterStatus_Unknown:
                    LedDisplayController_Write_StatusLeds(STATUS_INDICATOR_LED, MASTER_UNKNOWN_COLOR);
                    LedDisplayController_Write_StatusLeds(BLUETOOTH_INDICATOR_LED, BLE_OFF_COLOR);
                    break;

                case MasterStatus_NotConfigured:
                    LedDisplayController_Write_StatusLeds(STATUS_INDICATOR_LED, MASTER_NOT_CONFIGURED_COLOR);
                    break;

                case MasterStatus_Operational:
                    LedDisplayController_Write_StatusLeds(STATUS_INDICATOR_LED, MASTER_OPERATIONAL_COLOR);
                    break;

                case MasterStatus_Controlled:
                    LedDisplayController_Write_StatusLeds(STATUS_INDICATOR_LED, MASTER_CONTROLLED_COLOR);
                    break;

                case MasterStatus_Configuring:
                    LedDisplayController_Write_StatusLeds(STATUS_INDICATOR_LED, MASTER_CONFIGURING_COLOR);
                    break;

                case MasterStatus_Updating:
                    LedDisplayController_Write_StatusLeds(STATUS_INDICATOR_LED, MASTER_UPDATING_COLOR);
                    LedDisplayController_Write_StatusLeds(BLUETOOTH_INDICATOR_LED, BLE_OFF_COLOR);
                    break;
            }

            /* apply ring led */
            for (uint32_t i = 0u; i < 12u; i++)
            {
                LedDisplayController_Write_RingLeds(
                    i, // only write ring leds, not status leds
                    LedDisplayController_Read_RingLedsIn(i)
                );
            }
            break;

        case LedDisplayMode_SwitchedOff:
            LedDisplayController_Write_StatusLeds(MAIN_BATTERY_INDICATOR_LED, _display_main_battery_while_off());
            break;

        case LedDisplayMode_LowBattery:
            LedDisplayController_Write_StatusLeds(MAIN_BATTERY_INDICATOR_LED, _display_main_battery());
            break;
    }

    _previous_display_mode = current_display_mode;
    /* End User Code Section: Update:run Start */
    /* Begin User Code Section: Update:run End */

    /* End User Code Section: Update:run End */
}

__attribute__((weak))
void LedDisplayController_Write_MaxBrightness(uint8_t value)
{
    (void) value;
    /* Begin User Code Section: MaxBrightness:write Start */

    /* End User Code Section: MaxBrightness:write Start */
    /* Begin User Code Section: MaxBrightness:write End */

    /* End User Code Section: MaxBrightness:write End */
}

__attribute__((weak))
void LedDisplayController_Write_RingLeds(uint32_t index, rgb_t value)
{
    (void) value;
    ASSERT(index < 12);
    /* Begin User Code Section: RingLeds:write Start */

    /* End User Code Section: RingLeds:write Start */
    /* Begin User Code Section: RingLeds:write End */

    /* End User Code Section: RingLeds:write End */
}

__attribute__((weak))
void LedDisplayController_Write_StatusLeds(uint32_t index, rgb_t value)
{
    (void) value;
    ASSERT(index < 4);
    /* Begin User Code Section: StatusLeds:write Start */

    /* End User Code Section: StatusLeds:write Start */
    /* Begin User Code Section: StatusLeds:write End */

    /* End User Code Section: StatusLeds:write End */
}

__attribute__((weak))
BluetoothStatus_t LedDisplayController_Read_BluetoothStatus(void)
{
    /* Begin User Code Section: BluetoothStatus:read Start */

    /* End User Code Section: BluetoothStatus:read Start */
    /* Begin User Code Section: BluetoothStatus:read End */

    /* End User Code Section: BluetoothStatus:read End */
    return BluetoothStatus_Inactive;
}

__attribute__((weak))
uint8_t LedDisplayController_Read_DefaultBrightness(void)
{
    /* Begin User Code Section: DefaultBrightness:read Start */

    /* End User Code Section: DefaultBrightness:read Start */
    /* Begin User Code Section: DefaultBrightness:read End */

    /* End User Code Section: DefaultBrightness:read End */
    return 24;
}

__attribute__((weak))
uint8_t LedDisplayController_Read_LowBatteryBrightness(void)
{
    /* Begin User Code Section: LowBatteryBrightness:read Start */

    /* End User Code Section: LowBatteryBrightness:read Start */
    /* Begin User Code Section: LowBatteryBrightness:read End */

    /* End User Code Section: LowBatteryBrightness:read End */
    return 10;
}

__attribute__((weak))
bool LedDisplayController_Read_MainBatteryDetected(void)
{
    /* Begin User Code Section: MainBatteryDetected:read Start */

    /* End User Code Section: MainBatteryDetected:read Start */
    /* Begin User Code Section: MainBatteryDetected:read End */

    /* End User Code Section: MainBatteryDetected:read End */
    return false;
}

__attribute__((weak))
uint8_t LedDisplayController_Read_MainBatteryLevel(void)
{
    /* Begin User Code Section: MainBatteryLevel:read Start */

    /* End User Code Section: MainBatteryLevel:read Start */
    /* Begin User Code Section: MainBatteryLevel:read End */

    /* End User Code Section: MainBatteryLevel:read End */
    return 0u;
}

__attribute__((weak))
bool LedDisplayController_Read_MainBatteryLow(void)
{
    /* Begin User Code Section: MainBatteryLow:read Start */

    /* End User Code Section: MainBatteryLow:read Start */
    /* Begin User Code Section: MainBatteryLow:read End */

    /* End User Code Section: MainBatteryLow:read End */
    return false;
}

__attribute__((weak))
ChargerState_t LedDisplayController_Read_MainBatteryStatus(void)
{
    /* Begin User Code Section: MainBatteryStatus:read Start */

    /* End User Code Section: MainBatteryStatus:read Start */
    /* Begin User Code Section: MainBatteryStatus:read End */

    /* End User Code Section: MainBatteryStatus:read End */
    return ChargerState_NotPluggedIn;
}

__attribute__((weak))
MasterStatus_t LedDisplayController_Read_MasterStatus(void)
{
    /* Begin User Code Section: MasterStatus:read Start */

    /* End User Code Section: MasterStatus:read Start */
    /* Begin User Code Section: MasterStatus:read End */

    /* End User Code Section: MasterStatus:read End */
    return MasterStatus_Unknown;
}

__attribute__((weak))
uint8_t LedDisplayController_Read_MotorBatteryLevel(void)
{
    /* Begin User Code Section: MotorBatteryLevel:read Start */

    /* End User Code Section: MotorBatteryLevel:read Start */
    /* Begin User Code Section: MotorBatteryLevel:read End */

    /* End User Code Section: MotorBatteryLevel:read End */
    return 0u;
}

__attribute__((weak))
bool LedDisplayController_Read_MotorBatteryPresent(void)
{
    /* Begin User Code Section: MotorBatteryPresent:read Start */

    /* End User Code Section: MotorBatteryPresent:read Start */
    /* Begin User Code Section: MotorBatteryPresent:read End */

    /* End User Code Section: MotorBatteryPresent:read End */
    return false;
}

__attribute__((weak))
int16_t LedDisplayController_Read_MotorDriveValues(uint32_t index)
{
    ASSERT(index < 6);
    /* Begin User Code Section: MotorDriveValues:read Start */

    /* End User Code Section: MotorDriveValues:read Start */
    /* Begin User Code Section: MotorDriveValues:read End */

    /* End User Code Section: MotorDriveValues:read End */
    return 0;
}

__attribute__((weak))
uint8_t LedDisplayController_Read_PowerOffBrightness(void)
{
    /* Begin User Code Section: PowerOffBrightness:read Start */

    /* End User Code Section: PowerOffBrightness:read Start */
    /* Begin User Code Section: PowerOffBrightness:read End */

    /* End User Code Section: PowerOffBrightness:read End */
    return 10;
}

__attribute__((weak))
rgb_t LedDisplayController_Read_RingLedsIn(uint32_t index)
{
    ASSERT(index < 12);
    /* Begin User Code Section: RingLedsIn:read Start */

    /* End User Code Section: RingLedsIn:read Start */
    /* Begin User Code Section: RingLedsIn:read End */

    /* End User Code Section: RingLedsIn:read End */
    return (rgb_t){0, 0, 0};
}

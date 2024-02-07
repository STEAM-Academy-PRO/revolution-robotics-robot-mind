#include "MotorDriver_8833.h"
#include "utils.h"

/* Begin User Code Section: Declarations */
#include <peripheral_clk_config.h>
#include <hal_init.h>
#include <tc_lite.h>
#include <hal_gpio.h>
#include "atmel_start_pins.h"
#include "libraries/functions.h"

#define NUM_MOTORS 6
#define MOTOR_SPEED_RESOLUTION 200

/*
 * In order to know if motor is attached to the motor port or not, we apply
 * very small test load on the motor driver and hope to see change in current
 * draw on the motor driver's current sense (AIN) pin.
 * TEST_LOAD_MOTOR_SPEED regulates how little is the test load. Ideally it
 * shoule be so small that the motor even did not move
 */
static uint8_t test_load_motor_speed = 0;

#define MOTOR_DRV_CHAN_A 0
#define MOTOR_DRV_CHAN_B 1

static Tc* const timers[NUM_MOTORS] = {
    TC0,
    TC1,
    TC2,
    TC3,
    TC4,
    TC5
};

/*
 * Array of bool flags telling if test load is enabled for a particular
 * motor port
 */
static bool motor_test_load_enabled[NUM_MOTORS] = { 0 };

/*
 * Motor drivers are created on rrrc_worklogic side, here we save pointer to
 * them to refer in this component.
 * drivers_ref_count indicates array length under the pointer
 */
static MotorDriver_8833_t *drivers_ref = NULL;
static int drivers_ref_count = 0;

static void drv8833_set_speed(MotorDriver_8833_Channel_t* channel, const int16_t speed)
{
    if (speed != channel->prev_speed)
    {
        channel->prev_speed = speed;

        /*
         * - if speed is negative, pwm_1 holds the absolute value, otherwise pwm_0
         * - subtraction from max is because we want to drive motors using slow decay
         */
        const uint8_t pwm_0 = MOTOR_SPEED_RESOLUTION - constrain_int16(speed, 0, MOTOR_SPEED_RESOLUTION);
        const uint8_t pwm_1 = MOTOR_SPEED_RESOLUTION + constrain_int16(speed, -MOTOR_SPEED_RESOLUTION, 0); // constrain first to avoid -128 overflowing

        hri_tccount8_write_CC_reg(timers[channel->timer], channel->ch1, pwm_0);
        hri_tccount8_write_CC_reg(timers[channel->timer], channel->ch2, pwm_1);
    }
}

/**
 * Configure the given pin as a TC waveform output pin (function E)
 */
static void configure_wo_pin(const uint8_t pin)
{
    gpio_set_pin_direction(pin, GPIO_DIRECTION_OFF);
    gpio_set_pin_function(pin, GPIO_PIN_FUNCTION_E);
}

void MotorDriver_8833_InitDriver(MotorDriver_8833_t *driver)
{
    configure_wo_pin(driver->pwm_a.pin1);
    configure_wo_pin(driver->pwm_a.pin2);
    configure_wo_pin(driver->pwm_b.pin1);
    configure_wo_pin(driver->pwm_b.pin2);

    gpio_set_pin_direction(driver->fault, GPIO_DIRECTION_IN);
    gpio_set_pin_function(driver->fault, GPIO_PIN_FUNCTION_OFF);
    gpio_set_pin_pull_mode(driver->fault, GPIO_PULL_OFF);

    gpio_set_pin_direction(driver->n_sleep, GPIO_DIRECTION_OUT);
    gpio_set_pin_function(driver->n_sleep, GPIO_PIN_FUNCTION_OFF);
    gpio_set_pin_pull_mode(driver->n_sleep, GPIO_PULL_OFF);

    /* Initialization of ISEN pins is done in ADC Init */

    gpio_set_pin_level(driver->n_sleep, false);

    hri_tc_set_DBGCTRL_DBGRUN_bit(timers[driver->pwm_a.timer]);
    hri_tc_set_DBGCTRL_DBGRUN_bit(timers[driver->pwm_b.timer]);

    hri_tccount8_write_PER_reg(timers[driver->pwm_a.timer], MOTOR_SPEED_RESOLUTION - 1u);
    hri_tccount8_write_PER_reg(timers[driver->pwm_b.timer], MOTOR_SPEED_RESOLUTION - 1u);

    /* set a random speed to force updating the counters */
    driver->pwm_a.prev_speed = 1;
    driver->pwm_b.prev_speed = 1;
    drv8833_set_speed(&driver->pwm_a, 0);
    drv8833_set_speed(&driver->pwm_b, 0);
}

void MotorDriver_8833_Run_OnDriverInit(MotorDriver_8833_t* drivers,
    int num_drivers)
{
    for (int i = 0; i < num_drivers; ++i)
    {
      MotorDriver_8833_InitDriver(&drivers[i]);
    }
    drivers_ref = drivers;
    drivers_ref_count =  num_drivers;
}

static bool *MotorDriver_8833_GetTestLoadEnabledFlag(int driver_idx,
    int driver_channel)
{
    if (driver_idx > 2 || driver_channel > 1)
      return NULL;

    return &motor_test_load_enabled[driver_idx * 2 + driver_channel];
}

static bool MotorDriver_8833_IsTestLoadEnabled(int driver_idx,
    int driver_channel)
{
    bool *enabled_flag;
    enabled_flag = MotorDriver_8833_GetTestLoadEnabledFlag(
        driver_idx, driver_channel);

    if (!enabled_flag)
    {
        return false;
    }

    return *enabled_flag;
}

static bool MotorDriver_8833_SetTestLoadEna(int driver_idx, int driver_channel,
    uint8_t test_power, bool enable)
{
    MotorDriver_8833_t *driver;
    MotorDriver_8833_Channel_t *channel;
    bool *enabled_flag = NULL;

    if (driver_idx >= drivers_ref_count)
    {
        return false;
    }

    enabled_flag = MotorDriver_8833_GetTestLoadEnabledFlag(driver_idx,
        driver_channel);

    if (!enabled_flag)
    {
        return false;
    }

    driver = &drivers_ref[driver_idx];

    channel = &driver->pwm_a;

    if (driver_channel == 1)
    {
        channel = &driver->pwm_b;
    }

    if (enable)
    {
        if (*enabled_flag)
        {
            return false;
        }

        *enabled_flag = true;
        test_load_motor_speed = test_power;
        drv8833_set_speed(channel, test_load_motor_speed);
        gpio_set_pin_level(driver->n_sleep, true);
    }
    else
    {
        if (!*enabled_flag)
        {
            return false;
        }

        *enabled_flag = false;
        test_load_motor_speed = 0;

        drv8833_set_speed(channel, 0);
        gpio_set_pin_level(driver->n_sleep, false);
    }
    return true;
}

bool MotorDriver_8833_TestLoadStart(int driver_idx, int driver_channel, uint8_t test_power)
{
    return MotorDriver_8833_SetTestLoadEna(driver_idx, driver_channel, test_power, true);
}

bool MotorDriver_8833_TestLoadStop(int driver_idx, int driver_channel)
{
    return MotorDriver_8833_SetTestLoadEna(driver_idx, driver_channel, 0, false);
}

void MotorDriver_8833_Run_OnUpdate(MotorDriver_8833_t* driver)
{
    if (!driver->has_fault)
    {
        driver->has_fault = gpio_get_pin_level(driver->fault) == false;

        if (driver->has_fault)
        {
            MotorDriver_8833_Call_OnFault(driver);
        }
    }

    if (driver->has_fault)
    {
        /* false = sleep mode active */
        gpio_set_pin_level(driver->n_sleep, false);

        drv8833_set_speed(&driver->pwm_a, 0);
        drv8833_set_speed(&driver->pwm_b, 0);
    }
    else
    {
        int16_t speed_a;
        int16_t speed_b;

        if (MotorDriver_8833_IsTestLoadEnabled(driver->idx, MOTOR_DRV_CHAN_A))
        {
            speed_a = test_load_motor_speed;
        }
        else
        {
            speed_a = MotorDriver_8833_Read_DriveRequest_ChannelA(driver);
        }
        if (MotorDriver_8833_IsTestLoadEnabled(driver->idx, MOTOR_DRV_CHAN_B))
        {
            speed_b = test_load_motor_speed;
        }
        else
        {
            speed_b = MotorDriver_8833_Read_DriveRequest_ChannelB(driver);
        }

        /* set sleep mode if not driven (false = sleep mode active) */
        gpio_set_pin_level(driver->n_sleep, speed_a != 0 || speed_b != 0);

        drv8833_set_speed(&driver->pwm_a, speed_a);
        drv8833_set_speed(&driver->pwm_b, speed_b);
    }
}

void MotorDriver_8833_Run_FaultCleared(MotorDriver_8833_t* driver)
{
    driver->has_fault = false;
}

__attribute__((weak))
void MotorDriver_8833_Call_OnFault(MotorDriver_8833_t* driver)
{
    MotorDriver_8833_Run_FaultCleared(driver);
}

__attribute__((weak))
int16_t MotorDriver_8833_Read_DriveRequest_ChannelA(MotorDriver_8833_t* driver)
{
    (void) driver;

    return 0;
}

__attribute__((weak))
int16_t MotorDriver_8833_Read_DriveRequest_ChannelB(MotorDriver_8833_t* driver)
{
    (void) driver;

    return 0;
}
/* End User Code Section: Declarations */

void MotorDriver_8833_Run_OnInit(void)
{
    /* Begin User Code Section: OnInit:run Start */
    hri_mclk_set_APBAMASK_TC0_bit(MCLK);
    hri_mclk_set_APBAMASK_TC1_bit(MCLK);
    hri_mclk_set_APBBMASK_TC2_bit(MCLK);
    hri_mclk_set_APBBMASK_TC3_bit(MCLK);
    hri_mclk_set_APBCMASK_TC4_bit(MCLK);
    hri_mclk_set_APBCMASK_TC5_bit(MCLK);

    hri_gclk_write_PCHCTRL_reg(GCLK, TC0_GCLK_ID,
        CONF_GCLK_TC0_SRC | (1 << GCLK_PCHCTRL_CHEN_Pos));
    hri_gclk_write_PCHCTRL_reg(GCLK, TC1_GCLK_ID,
        CONF_GCLK_TC1_SRC | (1 << GCLK_PCHCTRL_CHEN_Pos));
    hri_gclk_write_PCHCTRL_reg(GCLK, TC2_GCLK_ID,
        CONF_GCLK_TC2_SRC | (1 << GCLK_PCHCTRL_CHEN_Pos));
    hri_gclk_write_PCHCTRL_reg(GCLK, TC3_GCLK_ID,
        CONF_GCLK_TC3_SRC | (1 << GCLK_PCHCTRL_CHEN_Pos));
    hri_gclk_write_PCHCTRL_reg(GCLK, TC4_GCLK_ID,
        CONF_GCLK_TC4_SRC | (1 << GCLK_PCHCTRL_CHEN_Pos));
    hri_gclk_write_PCHCTRL_reg(GCLK, TC5_GCLK_ID,
        CONF_GCLK_TC5_SRC | (1 << GCLK_PCHCTRL_CHEN_Pos));

    TIMER_0_init();
    TIMER_1_init();
    TIMER_2_init();
    TIMER_3_init();
    TIMER_4_init();
    TIMER_5_init();

    /*
     * Event system EVSYS is used for 2 purposes:
     * 1. Start all timers synchronously (in the same time), by using a signle
     *    start trigger to start all of them. This is done in the first block
     *    of code below, by routing  CHANNEL 0 events to TC0,1,2,.. event input
     *    In code, that exectutes later, CHANNEL 0 is 'software triggered' to
     *    generate an EVENT on CHANNEL 0, which will then propagate to all
     *    timer counter peripheral instances in the same time.
     * 2. Each start of new PWM period will send an EVENT to CHANNEL 1, which
     *    will trigger ADC conversions on both ADC modules, see code in ADC.c
     */
    hri_evsys_set_USER_CHANNEL_bf(EVSYS, EVSYS_ID_USER_TC0_EVU,
        EVSYS_USER_CHANNEL(EVSYS_SWEVT_CHANNEL0));
    hri_evsys_set_USER_CHANNEL_bf(EVSYS, EVSYS_ID_USER_TC1_EVU,
        EVSYS_USER_CHANNEL(EVSYS_SWEVT_CHANNEL0));
    hri_evsys_set_USER_CHANNEL_bf(EVSYS, EVSYS_ID_USER_TC2_EVU,
        EVSYS_USER_CHANNEL(EVSYS_SWEVT_CHANNEL0));
    hri_evsys_set_USER_CHANNEL_bf(EVSYS, EVSYS_ID_USER_TC3_EVU,
        EVSYS_USER_CHANNEL(EVSYS_SWEVT_CHANNEL0));
    hri_evsys_set_USER_CHANNEL_bf(EVSYS, EVSYS_ID_USER_TC4_EVU,
        EVSYS_USER_CHANNEL(EVSYS_SWEVT_CHANNEL0));
    hri_evsys_set_USER_CHANNEL_bf(EVSYS, EVSYS_ID_USER_TC5_EVU,
        EVSYS_USER_CHANNEL(EVSYS_SWEVT_CHANNEL0));

    hri_evsys_write_CHANNEL_reg(EVSYS, 0, EVSYS_CHANNEL_ONDEMAND
        | EVSYS_CHANNEL_PATH_RESYNCHRONIZED
        | EVSYS_CHANNEL_EDGSEL_RISING_EDGE);

    hri_evsys_write_CHANNEL_reg(EVSYS, 1, EVSYS_CHANNEL_ONDEMAND
        | EVSYS_CHANNEL_PATH_RESYNCHRONIZED
        | EVSYS_CHANNEL_EDGSEL_RISING_EDGE
        | EVSYS_CHANNEL_EVGEN(EVSYS_ID_GEN_TC0_OVF));
    /* End User Code Section: OnInit:run Start */
    /* Begin User Code Section: OnInit:run End */

    /* End User Code Section: OnInit:run End */
}

void MotorDriver_8833_Run_StartISR(void)
{
    /* Begin User Code Section: StartISR:run Start */
    hri_evsys_write_SWEVT_reg(EVSYS, EVSYS_SWEVT_CHANNEL0);

    /* End User Code Section: StartISR:run Start */
    /* Begin User Code Section: StartISR:run End */

    /* End User Code Section: StartISR:run End */
}

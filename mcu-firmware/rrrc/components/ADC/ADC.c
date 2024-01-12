#include "ADC.h"
#include "utils.h"
#include "utils_assert.h"

/* Begin User Code Section: Declarations */
#include "atmel_start_pins.h"
#include <hal_adc_async.h>
#include <peripheral_clk_config.h>

#include <stdbool.h>
#include <math.h>

/* Number of ADC instances on the MCU, like ADC0, ADC1, etc */
#define NUM_ADC_MODULES 2

/* Number of motor slots */
#define NUM_MOTORS 6

/* Number of sensor slots */
#define NUM_SENSORS 4

/*
 * Motor detected condition is to receive ADC value greater than
 * THRESHOLD_BASE + THRESHOLD_DELTA. This is the default DELTA if 0 is passed
 * in ADC_DetectMotorStart argument.
 */
#define ADC_DETECT_MOTOR_THRES_DELTA_DEF 20

#define INVALID_MOTOR_ADC_CHANNEL 0xff

/* Motor detection algo is finished/not requested */
#define ADC_DETECT_MOTOR_STATE_NONE 0

/* Motor detection algo is requested to start */
#define ADC_DETECT_MOTOR_STATE_START_REQUEST 1

/* Motor detection algo is requested to stop */
#define ADC_DETECT_MOTOR_STATE_STOP_REQUEST 2

/* Motor detection algo is running currently */
#define ADC_DETECT_MOTOR_STATE_IN_PROGRESS 3

/*
 * Maximum ADC channel index on the MCU, example channel id is ADC0/AIN15,
 * where 15 is maximum for this chip
 */
#define MAX_ADC_CHANNEL_INDEX 15

static const adc_pos_input_t adc0_channels[] =
{
    S0_ADC_CH,
    M1_ISEN_CH,
    M3_ISEN_CH,
    M4_ISEN_CH
};

#define ADC0_IDX_SENSOR_0 0
#define ADC0_IDX_MOTOR_1  1
#define ADC0_IDX_MOTOR_3  2
#define ADC0_IDX_MOTOR_4  3

#define ADC1_IDX_SENSOR_1 0
#define ADC1_IDX_SENSOR_2 1
#define ADC1_IDX_SENSOR_3 2
#define ADC1_IDX_MOTOR_0  3
#define ADC1_IDX_MOTOR_2  4
#define ADC1_IDX_MOTOR_5  5
#define ADC1_IDX_MAIN_BAT_VOLTAGE 6
#define ADC1_IDX_MOTOR_BAT_VOLTAGE 7

static const adc_pos_input_t adc1_channels[] =
{
    S1_ADC_CH,
    S2_ADC_CH,
    S3_ADC_CH,
    M0_ISEN_CH,
    M2_ISEN_CH,
    M5_ISEN_CH,
    ADC_CH_BAT_VOLTAGE,
    ADC_CH_MOT_VOLTAGE
};

static const uint8_t adc0_samples[ARRAY_SIZE(adc0_channels)] = {
    0,
    0,
    0,
    0
};

static const uint8_t adc1_samples[ARRAY_SIZE(adc1_channels)] = {
    0,
    0,
    0,
    0,
    0,
    0,
    63,
    63
};

const int motor_idx_to_brain_map[NUM_MOTORS] = {
  3, 4, 5, 2, 1, 0
};

static const uint8_t adc0_initial_meas_channels[] = {
    ADC0_IDX_MOTOR_1,
    ADC0_IDX_MOTOR_1,
    ADC0_IDX_MOTOR_3,
    ADC0_IDX_MOTOR_3,
    ADC0_IDX_MOTOR_4,
    ADC0_IDX_MOTOR_4
};

static const uint8_t adc1_initial_meas_channels[] = {
    ADC1_IDX_MOTOR_0,
    ADC1_IDX_MOTOR_0,
    ADC1_IDX_MOTOR_2,
    ADC1_IDX_MOTOR_2,
    ADC1_IDX_MOTOR_5,
    ADC1_IDX_MOTOR_5
};

typedef struct
{
    Adc *hw;
    /* Filled by lib */
    struct adc_async_descriptor hw_descriptor;

    /* Current ADC being sampled */
    uint32_t current_channel;

    /* Number of ADC channels used by application for this module */
    int num_channels;

    /* Mapping from in-app channel indices to mcu ADC channel numbers */
    adc_pos_input_t channels[MAX_ADC_CHANNEL_INDEX + 1];
    uint8_t samples[MAX_ADC_CHANNEL_INDEX + 1];

    /* Last sampled data */
    uint16_t data[MAX_ADC_CHANNEL_INDEX + 1];

    int initial_meas_idx;
    uint16_t initial_meas_channels[6];
    uint16_t initial_meas_values[6];

    /*
     * There is a big variation in conversion result values, received from
     * different ADCs (ADC0 or ADC1) under same conditions when motor is
     * detached from the port and no current flows.
     * threshold is value measured when current is not flowing + some added
     * small delta.
     * When motor receives current, the value immediately grows, so making a
     * threshold slightly bigger than the measured minimum is the way to detect
     * increase of current and making a conclusion that the motor is attached.
     */
    uint16_t threshold_base;
} adc_context_t;

static adc_context_t adc_ctx[NUM_ADC_MODULES] = { 0 };
static int adc_init_completion = 0;

static int adc_detect_motor_state = ADC_DETECT_MOTOR_STATE_NONE;
static adc_context_t *adc_detect_motor_ctx = NULL;
static uint8_t adc_detect_motor_thres_delta = ADC_DETECT_MOTOR_THRES_DELTA_DEF;
static uint8_t adc_detect_motor_adc_channel = INVALID_MOTOR_ADC_CHANNEL;
static bool adc_detect_motor_detected = false;

#define ADC_MAX 4095
static inline float adc_to_mv(float x)
{
    return ((3300.0f / ADC_MAX) * x);
}

static void adc_conversion_complete(
    const struct adc_async_descriptor *const descr, uint16_t adc_data);

static void adc_initial_conversion_complete(
    const struct adc_async_descriptor *const descr, uint16_t adc_data);

static adc_context_t *adc_async_descr_to_ctx(
    const struct adc_async_descriptor *const descr)
{
    for (unsigned int i = 0; i < ARRAY_SIZE(adc_ctx); ++i)
    {
        if (&adc_ctx[i].hw_descriptor == descr)
        {
            return &adc_ctx[i];
        }
    }
    return NULL;
}

static void adc_detect_motor_chan_setup(adc_context_t *ctx,
    uint32_t channel_idx)
{
    /* Set ADC clock ticks per single sampling */
    hri_adc_write_SAMPCTRL_SAMPLEN_bf(ctx->hw, 63);

    /* Enable accumumlation of 512 samples */
    hri_adc_write_AVGCTRL_SAMPLENUM_bf(ctx->hw, ADC_AVGCTRL_SAMPLENUM_512_Val);
    hri_adc_write_CTRLB_RESSEL_bf(ctx->hw, ADC_CTRLB_RESSEL_16BIT_Val);

    /* Select ADC channel, it should then run automatically */
    hri_adc_write_INPUTCTRL_MUXPOS_bf(ctx->hw, ctx->channels[channel_idx]);
}

#define BITFIELD_EXTRACT(__base) \
  (*((uint32_t *)__base ## _ADDR) & __base ## _Msk) >> __base ## _Pos

static void adc_calibrate(Adc *adc)
{
    uint32_t biascomp;
    uint32_t biasr2r;
    uint32_t biasrefbuf ;

    if (adc == ADC0)
    {
        /* ADC0 */
        biascomp = BITFIELD_EXTRACT(ADC0_FUSES_BIASCOMP);
        biasr2r = BITFIELD_EXTRACT(ADC0_FUSES_BIASR2R);
        biasrefbuf = BITFIELD_EXTRACT(ADC0_FUSES_BIASREFBUF);
    }
    else
    {
        /* ADC1 */
        biascomp = BITFIELD_EXTRACT(ADC1_FUSES_BIASCOMP);
        biasr2r = BITFIELD_EXTRACT(ADC1_FUSES_BIASR2R);
        biasrefbuf = BITFIELD_EXTRACT(ADC1_FUSES_BIASREFBUF);
    }

    hri_adc_write_CALIB_BIASCOMP_bf(adc, biascomp);
    hri_adc_write_CALIB_BIASR2R_bf(adc, biasr2r);
    hri_adc_write_CALIB_BIASREFBUF_bf(adc, biasrefbuf);
}

static void adc_convert_channel(adc_context_t *ctx, uint32_t channel_idx)
{
    ctx->current_channel = channel_idx;

    hri_adc_set_SAMPCTRL_SAMPLEN_bf(ctx->hw,
        ctx->samples[ctx->current_channel]);

    adc_async_set_inputs(&ctx->hw_descriptor,
        ctx->channels[ctx->current_channel], ADC_CHN_INT_GND);
}

static void adc_init_events(adc_context_t *ctx)
{
    hri_evsys_user_reg_t evsys_user_event;

    /*
     * ADC conversions are synchronised with PWM counters that control motor
     * drivers. Every new conversion starts when TC0 counter reaches period
     * value, set in TC0.PER. This should increase quality of motor current
     * measurements.
     * TODO: this needs to be rechecked because details are lost.
     *
     * Below EVSYS is set to redirect signals coming to EVSYS CHANNEL 1
     * to ADC start trigger. Initialization code in MotorDriver_8833.c sets up
     * second part of the signal commutation by outputting timer's overflow /
     * underflow event to EVSYS CHANNEL 1.
     */

    if (ctx->hw == ADC0)
    {
        evsys_user_event = EVSYS_ID_USER_ADC0_START;
    }
    else
    {
        evsys_user_event = EVSYS_ID_USER_ADC1_START;
    }

    hri_evsys_set_USER_CHANNEL_bf(EVSYS, evsys_user_event,
        EVSYS_USER_CHANNEL(EVSYS_SWEVT_CHANNEL1));
}

static void adc_context_init(adc_context_t *ctx, Adc *hw, int num_channels,
    const adc_pos_input_t *channels, const uint8_t *samples,
    const uint8_t *initial_meas_channels)
{
    ctx->hw = hw;
    ctx->current_channel = 0;
    ctx->num_channels = num_channels;

    for (int i = 0; i < num_channels; ++i)
    {
        ctx->channels[i]= channels[i];
        ctx->samples[i]= samples[i];
        ctx->data[i] = 0;
    }

    ctx->initial_meas_idx = 0;
    for (unsigned int i = 0; i < ARRAY_SIZE(ctx->initial_meas_channels); ++i)
    {
      ctx->initial_meas_channels[i] = initial_meas_channels[i];
      ctx->initial_meas_values[i] = 0;
    }

    adc_async_init(&ctx->hw_descriptor, ctx->hw);

    /* This is required to run ADC when halted at debug */
    hri_adc_set_DBGCTRL_DBGRUN_bit(ctx->hw);

    adc_async_register_callback(&ctx->hw_descriptor,
        ADC_ASYNC_CONVERT_CB, adc_initial_conversion_complete);

    adc_calibrate(ctx->hw);

    adc_async_enable(&ctx->hw_descriptor);

    /* Setup initial measurement conversion  */
    adc_detect_motor_chan_setup(ctx, ctx->initial_meas_channels[0]);

    /* Run initial measurements by manually triggering with SWTRIG */
    hri_adc_set_SWTRIG_START_bit(ctx->hw);
}

static void adc_calc_threshold_base(adc_context_t *ctx)
{
    uint32_t sum = 0;

    for (unsigned int i = 0; i < ARRAY_SIZE(ctx->initial_meas_values); ++i)
    {
        sum += ctx->initial_meas_values[i];
    }

    ctx->threshold_base = sum / ARRAY_SIZE(ctx->initial_meas_values);
}

static void adc_calc_threshold_bases(void)
{
    for (unsigned int i = 0; i < ARRAY_SIZE(adc_ctx); ++i)
    {
        adc_calc_threshold_base(&adc_ctx[i]);
    }
}

static void adc_init_finalize(adc_context_t *ctx)
{
    hri_adc_clear_CTRLA_ENABLE_bit(ctx->hw);
    adc_init_events(ctx);

    adc_async_register_callback(&ctx->hw_descriptor,
        ADC_ASYNC_CONVERT_CB, adc_conversion_complete);

    hri_adc_write_AVGCTRL_SAMPLENUM_bf(ctx->hw, ADC_AVGCTRL_SAMPLENUM_1_Val);
    hri_adc_write_CTRLB_RESSEL_bf(ctx->hw, ADC_CTRLB_RESSEL_12BIT_Val);

    hri_adc_set_CTRLA_ENABLE_bit(ctx->hw);
    adc_init_completion++;
    if (adc_init_completion == 4)
    {
        adc_calc_threshold_bases();
        /* Enable timer counters TCx to synchronise ADC values + motor PWM */
        ADC_RaiseEvent_InitDoneISR();
    }
}

static void adc_initial_conversion_complete(
    const struct adc_async_descriptor *const descr, uint16_t adc_data)
{
    adc_context_t *ctx = adc_async_descr_to_ctx(descr);

    if (!ctx)
    {
        return;
    }

    ctx->initial_meas_values[ctx->initial_meas_idx] = adc_data;
    ctx->initial_meas_idx++;

    if (ctx->initial_meas_idx == ARRAY_SIZE(ctx->initial_meas_channels))
    {
      adc_init_completion++;
      if (adc_init_completion == 2)
      {
          adc_init_finalize(&adc_ctx[0]);
          adc_init_finalize(&adc_ctx[1]);
      }
      return;
    }

    adc_detect_motor_chan_setup(ctx,
        ctx->initial_meas_channels[ctx->initial_meas_idx]);

    hri_adc_set_SWTRIG_START_bit(ctx->hw);
}

/*
 * Sensor and motor ports are sensed from different ADC modules ADC0, ADC1,
 * this helper function knows where to take raw ADC results based on port
 * index.
 * If given index is too big, 0 is returned
 */
static uint16_t get_sensor_data_by_idx(int idx)
{
  const uint16_t *adc0_data = adc_ctx[0].data;
  const uint16_t *adc1_data = adc_ctx[1].data;

  if (idx >= NUM_SENSORS)
    return 0;

  switch(idx)
  {
    case 0: return adc1_data[ADC1_IDX_SENSOR_3];
    case 1: return adc1_data[ADC1_IDX_SENSOR_2];
    case 2: return adc1_data[ADC1_IDX_SENSOR_1];
    case 3: return adc0_data[ADC0_IDX_SENSOR_0];
    default:return 0;
  }
}

static bool get_motor_adc_addr(int motor_idx, int *module, int *channel)
{
  if (motor_idx >= NUM_MOTORS || !module || !channel)
    return false;

  switch(motor_idx)
  {
    case 0: *module = 1; *channel = ADC1_IDX_MOTOR_0; return true;
    case 1: *module = 0; *channel = ADC0_IDX_MOTOR_1; return true;
    case 2: *module = 1; *channel = ADC1_IDX_MOTOR_2; return true;
    case 3: *module = 0; *channel = ADC0_IDX_MOTOR_3; return true;
    case 4: *module = 0; *channel = ADC0_IDX_MOTOR_4; return true;
    case 5: *module = 1; *channel = ADC1_IDX_MOTOR_5; return true;
    default: break;
  }
  return false;
}

/* See description of 'get_sensor_data_by_idx' */
static uint16_t get_motor_data_by_idx(int motor_idx)
{
  const uint16_t *adc0_data = adc_ctx[0].data;
  const uint16_t *adc1_data = adc_ctx[1].data;
  const uint16_t *adc_x_data = NULL;
  int module = 0;
  int channel = 0;

  if (motor_idx >= NUM_MOTORS)
  {
      return 0;
  }

  if (!get_motor_adc_addr(motor_idx, &module, &channel))
  {
      return 0;
  }

  if (module == 0)
  {
      adc_x_data = adc0_data;
  }
  else if (module == 1)
  {
      adc_x_data = adc1_data;
  }
  else
  {
      return 0;
  }

  if (channel > MAX_ADC_CHANNEL_INDEX)
  {
      return 0;
  }

  return adc_x_data[channel];
}

bool ADC_DetectMotorStart(int motor_idx, uint8_t threshold_delta)
{
    int motor_adc_channel;
    int adc_module;

    adc_context_t *ctx = NULL;

    /* Check that this motor is listened with this ADC module */
    if (motor_idx >= NUM_MOTORS)
    {
      return false;
    }

    /* Check that previous motor detect was stopped */
    if (adc_detect_motor_state != ADC_DETECT_MOTOR_STATE_NONE)
    {
      return false;
    }

    if (!get_motor_adc_addr(motor_idx, &adc_module, &motor_adc_channel)
        || (unsigned int)adc_module >= ARRAY_SIZE(adc_ctx)
        || motor_adc_channel > MAX_ADC_CHANNEL_INDEX)
    {
      return false;
    }

    if (threshold_delta == 0)
    {
        threshold_delta = ADC_DETECT_MOTOR_THRES_DELTA_DEF;
    }

    ctx = &adc_ctx[adc_module];

    CRITICAL_SECTION_ENTER();
    adc_detect_motor_thres_delta = threshold_delta;
    adc_detect_motor_state = ADC_DETECT_MOTOR_STATE_START_REQUEST;
    adc_detect_motor_adc_channel = motor_adc_channel;
    adc_detect_motor_ctx = ctx;
    adc_detect_motor_detected = false;
    CRITICAL_SECTION_LEAVE();
    return true;
}

void ADC_DetectMotorStop(void)
{
    CRITICAL_SECTION_ENTER();
    adc_detect_motor_state = ADC_DETECT_MOTOR_STATE_STOP_REQUEST;
    CRITICAL_SECTION_LEAVE();
}

bool ADC_DetectMotorDetected(void)
{
    return adc_detect_motor_detected;
}

static void adc_set_next_conversion(adc_context_t *ctx)
{
    if (ctx->current_channel < ctx->num_channels - 1u)
    {
        adc_convert_channel(ctx, ctx->current_channel + 1u);
    }
    else
    {
        adc_convert_channel(ctx, 0u);
    }
}

static void adc_detect_motor_stop(void)
{
    adc_context_t *ctx = adc_detect_motor_ctx;
    /* Threshold reached, switch back to normal conversion loop */
    adc_detect_motor_adc_channel = INVALID_MOTOR_ADC_CHANNEL;
    adc_detect_motor_state = ADC_DETECT_MOTOR_STATE_NONE;
    hri_adc_write_AVGCTRL_SAMPLENUM_bf(ctx->hw, ADC_AVGCTRL_SAMPLENUM_1_Val);
    hri_adc_write_CTRLB_RESSEL_bf(ctx->hw, ADC_CTRLB_RESSEL_12BIT_Val);
    adc_detect_motor_ctx = NULL;
}

static void adc_handle_motor_detect_conversion(adc_context_t *ctx,
    uint16_t adc_data)
{
    switch (adc_detect_motor_state)
    {
        case ADC_DETECT_MOTOR_STATE_START_REQUEST:
        {
            /* Collect previous measurement result */
            ctx->data[ctx->current_channel] = adc_data;

            /* Now start motor detection conversions */
            adc_detect_motor_chan_setup(adc_detect_motor_ctx,
                adc_detect_motor_adc_channel);
            adc_detect_motor_state = ADC_DETECT_MOTOR_STATE_IN_PROGRESS;
        }
        break;
        case ADC_DETECT_MOTOR_STATE_IN_PROGRESS:
        {
            uint16_t threshold = ctx->threshold_base
              + adc_detect_motor_thres_delta;

            if (adc_data >= threshold)
            {
                /*
                 * Motor detected, detection should now stop and switch
                 * to normal measurements
                 */
                adc_detect_motor_detected = true;
                adc_detect_motor_stop();
                adc_set_next_conversion(ctx);
            }
            /* Threshold not reached, continue detection */
        }
        break;

        /*
         * Feature user can request to stop detection before motor
         * is detected. In that case we should switch to normal conversion
         * from where we left off
         */
        case ADC_DETECT_MOTOR_STATE_STOP_REQUEST:
        {
            adc_detect_motor_stop();
            adc_set_next_conversion(ctx);
        }
        break;
        default: break;
    }
}

static void adc_conversion_complete(
    const struct adc_async_descriptor *const descr, uint16_t adc_data)
{
    uint32_t channel_idx;

    adc_context_t *ctx = adc_async_descr_to_ctx(descr);

    if (!ctx)
    {
        return;
    }

    channel_idx = ctx->current_channel;

    if (ctx == adc_detect_motor_ctx)
    {
        adc_handle_motor_detect_conversion(ctx, adc_data);
    }
    else
    {
        ctx->data[channel_idx] = adc_data;
        adc_set_next_conversion(ctx);
    }
}

/* End User Code Section: Declarations */

void ADC_Run_OnInit(void)
{
    /* Begin User Code Section: OnInit:run Start */

    /*
     * Start ADC0,ADC1 clocks is the first thing to do, otherwise ADC registers
     * are unresponsive
     */
    hri_mclk_set_APBDMASK_ADC0_bit(MCLK);
    hri_mclk_set_APBDMASK_ADC1_bit(MCLK);

    hri_gclk_write_PCHCTRL_reg(GCLK, ADC0_GCLK_ID,
        CONF_GCLK_ADC0_SRC | (1 << GCLK_PCHCTRL_CHEN_Pos));

    /* Init all motor driver GPIO pins */
    gpio_set_pin_function(S0_AIN, GPIO_PIN_FUNCTION_B);
    gpio_set_pin_function(S1_AIN, GPIO_PIN_FUNCTION_B);
    gpio_set_pin_function(S2_AIN, GPIO_PIN_FUNCTION_B);
    gpio_set_pin_function(S3_AIN, GPIO_PIN_FUNCTION_B);

    gpio_set_pin_function(MOTOR_DRIVER_0_CH_A_ISEN, GPIO_PIN_FUNCTION_B);
    gpio_set_pin_function(MOTOR_DRIVER_0_CH_B_ISEN, GPIO_PIN_FUNCTION_B);
    gpio_set_pin_function(MOTOR_DRIVER_1_CH_A_ISEN, GPIO_PIN_FUNCTION_B);
    gpio_set_pin_function(MOTOR_DRIVER_1_CH_B_ISEN, GPIO_PIN_FUNCTION_B);
    gpio_set_pin_function(MOTOR_DRIVER_2_CH_A_ISEN, GPIO_PIN_FUNCTION_B);
    gpio_set_pin_function(MOTOR_DRIVER_2_CH_B_ISEN, GPIO_PIN_FUNCTION_B);

    hri_gclk_write_PCHCTRL_reg(GCLK, ADC1_GCLK_ID,
        CONF_GCLK_ADC1_SRC | (1 << GCLK_PCHCTRL_CHEN_Pos));

    adc_context_init(&adc_ctx[0], ADC0, ARRAY_SIZE(adc0_channels),
        adc0_channels, adc0_samples, adc0_initial_meas_channels);

    adc_context_init(&adc_ctx[1], ADC1, ARRAY_SIZE(adc1_channels),
        adc1_channels, adc1_samples, adc1_initial_meas_channels);

    /* End User Code Section: OnInit:run Start */
    /* Begin User Code Section: OnInit:run End */

    /* End User Code Section: OnInit:run End */
}

void ADC_Run_Update(void)
{
    /* Begin User Code Section: Update:run Start */
    const uint16_t *adc1_data = adc_ctx[1].data;

    uint16_t raw_motor_bat_voltage = adc1_data[ADC1_IDX_MOTOR_BAT_VOLTAGE];
    uint16_t raw_main_bat_voltage = adc1_data[ADC1_IDX_MAIN_BAT_VOLTAGE];

    uint32_t motor_battery_voltage = lroundf(adc_to_mv(raw_motor_bat_voltage)
        * (130.0f / 30.0f));

    uint32_t main_battery_voltage = lroundf(adc_to_mv(raw_main_bat_voltage)
        * (340.0f / 240.0f));

    ADC_Write_MotorBatteryVoltage(motor_battery_voltage);
    ADC_Write_MainBatteryVoltage(main_battery_voltage);

    for (int i = 0; i < NUM_SENSORS; ++i)
    {
        uint16_t sensor_data = get_sensor_data_by_idx(i);

        ADC_Write_Sensor_ADC(i, sensor_data >> 4);
    }

    for (int i = 0; i < NUM_MOTORS; ++i)
    {
        uint16_t motor_current_raw = get_motor_data_by_idx(i);

        /*
         * On the 'brain' and on mobile app motor indices are not same as on
         * schematic, this firmware uses same indexing as in schematic, so we
         * must convert to 'brain' to output to slots. TODO: move this
         * mapping as far as possible to external interface
         */
        int brain_idx = motor_idx_to_brain_map[i];
        /* milli-volt / milli-Ohm -> Ampere */
        float motor_current = motor_current_raw / 120.0f;
        ADC_Write_MotorCurrent(brain_idx, motor_current);
    }
    /* End User Code Section: Update:run Start */
    /* Begin User Code Section: Update:run End */

    /* End User Code Section: Update:run End */
}

__attribute__((weak))
void ADC_RaiseEvent_InitDoneISR(void)
{
    /* Begin User Code Section: InitDoneISR:run Start */

    /* End User Code Section: InitDoneISR:run Start */
    /* Begin User Code Section: InitDoneISR:run End */

    /* End User Code Section: InitDoneISR:run End */
}

__attribute__((weak))
void ADC_Write_MainBatteryVoltage(Voltage_t value)
{
    (void) value;
    /* Begin User Code Section: MainBatteryVoltage:write Start */

    /* End User Code Section: MainBatteryVoltage:write Start */
    /* Begin User Code Section: MainBatteryVoltage:write End */

    /* End User Code Section: MainBatteryVoltage:write End */
}

__attribute__((weak))
void ADC_Write_MotorBatteryVoltage(Voltage_t value)
{
    (void) value;
    /* Begin User Code Section: MotorBatteryVoltage:write Start */

    /* End User Code Section: MotorBatteryVoltage:write Start */
    /* Begin User Code Section: MotorBatteryVoltage:write End */

    /* End User Code Section: MotorBatteryVoltage:write End */
}

__attribute__((weak))
void ADC_Write_MotorCurrent(uint32_t index, Current_t value)
{
    (void) value;
    ASSERT(index < 6);
    /* Begin User Code Section: MotorCurrent:write Start */

    /* End User Code Section: MotorCurrent:write Start */
    /* Begin User Code Section: MotorCurrent:write End */

    /* End User Code Section: MotorCurrent:write End */
}

__attribute__((weak))
void ADC_Write_Sensor_ADC(uint32_t index, uint8_t value)
{
    (void) value;
    ASSERT(index < 4);
    /* Begin User Code Section: Sensor_ADC:write Start */

    /* End User Code Section: Sensor_ADC:write Start */
    /* Begin User Code Section: Sensor_ADC:write End */

    /* End User Code Section: Sensor_ADC:write End */
}

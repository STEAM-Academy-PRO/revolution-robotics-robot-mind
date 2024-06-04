#include "scenario_handlers.h"

#include "CommonLibraries/functions.h"
#include "../RingLedDisplay.h"
#include <math.h>

#define RING_LEDS_AMOUNT ((uint8_t) 12u)
#define RING_LED_UPDATE_TIME ((uint32_t) 20u)

typedef struct {
    const rgb_t color;
    uint32_t time;
} breathing_data_t;

static breathing_data_t breathing_green_data = {
    .color = LED_GREEN
};

typedef struct {
    const rgb_t color;
    uint32_t time;
} spinning_color_data_t;

static spinning_color_data_t spinning_color_data = {
    .color = LED_RED
};

/* local function declarations */

static void ledRingOffWriter(void* data);
static void ledRingFrameWriter(void* data);
static void colorWheelWriter(void* data);
static void rainbowFadeWriter(void* data);
static void spinningColorWriter(void* data);
static void init_spinningColor(void* data);
static void init_time(void* data);
static void init_breathing(void* data);
static void breathing(void* data);
static void startup_indicator(void* data);

static void siren(void* data);
static void traffic_light(void* data);
static void bugIndicator(void* data);

static uint32_t time_data;

const indication_handler_t startup_indicator_scenario = {
    .name     = "",
    .init     = init_time,
    .update   = startup_indicator,
    .uninit   = NULL,
    .userData = &time_data
};

const indication_handler_t public_scenario_handlers[] =
{
    [RingLedScenario_Off] = {
        .name     = "RingLedOff",
        .init     = NULL,
        .update   = ledRingOffWriter,
        .uninit   = NULL,
        .userData = NULL
    },
    [RingLedScenario_UserFrame] = {
        .name     = "UserFrame",
        .init     = NULL,
        .update   = ledRingFrameWriter,
        .uninit   = NULL,
        .userData = NULL
    },
    [RingLedScenario_ColorWheel] = {
        .name     = "ColorWheel",
        .init     = init_time,
        .update   = colorWheelWriter,
        .uninit   = NULL,
        .userData = &time_data
    },
    [RingLedScenario_RainbowFade] = {
        .name     = "RainbowFade",
        .init     = init_time,
        .update   = rainbowFadeWriter,
        .uninit   = NULL,
        .userData = &time_data
    },
    [RingLedScenario_BusyIndicator] = {
        .name     = "BusyRing",
        .init     = init_spinningColor,
        .update   = spinningColorWriter,
        .uninit   = NULL,
        .userData = &spinning_color_data
    },
    [RingLedScenario_BreathingGreen] = {
        .name     = "BreathingGreen",
        .init     = init_breathing,
        .update   = breathing,
        .uninit   = NULL,
        .userData = &breathing_green_data
    },
    [RingLedScenario_Siren] = {
        .name     = "",
        .init     = init_time,
        .update   = siren,
        .uninit   = NULL,
        .userData = &time_data
    },
    [RingLedScenario_TrafficLight] = {
        .name     = "",
        .init     = init_time,
        .update   = traffic_light,
        .uninit   = NULL,
        .userData = &time_data
    },
    [RingLedScenario_BugIndicator] = {
        .name     = "",
        .init     = init_time,
        .update   = bugIndicator,
        .uninit   = NULL,
        .userData = &time_data
    }
};

static void init_time(void* data)
{
    uint32_t* time = (uint32_t*) data;

    *time = 0u;
}

static void startup_indicator(void* data)
{
    uint32_t* time = (uint32_t*) data;

    uint32_t n_leds = (uint32_t) ceilf(map_constrained(*time, 0, RingLedDisplay_Read_ExpectedStartupTime(), 0, 12));

    for (uint32_t i = 0u; i < n_leds; i++)
    {
        RingLedDisplay_Write_LedColor(i, (rgb_t) LED_YELLOW);
    }

    for (uint32_t i = n_leds; i < 12u; i++)
    {
        RingLedDisplay_Write_LedColor(i, (rgb_t) LED_OFF);
    }

    *time += RING_LED_UPDATE_TIME;
}

static void ledRingOffWriter(void* data)
{
    (void) data;
    for (uint32_t idx = 0u; idx < RING_LEDS_AMOUNT; idx++)
    {
        RingLedDisplay_Write_LedColor(idx, (rgb_t) LED_OFF);
    }
}

static void ledRingFrameWriter(void* data)
{
    (void) data;
    for (uint32_t idx = 0u; idx < RING_LEDS_AMOUNT; idx++)
    {
        RingLedDisplay_Write_LedColor(idx, RingLedDisplay_Read_UserColors(idx));
    }
}

static void colorWheelWriter(void* data)
{
    uint32_t* time = (uint32_t*) data;
    uint32_t phase = (*time * 6) / 20;

    *time += RING_LED_UPDATE_TIME;

    for (uint32_t i = 0u; i < RING_LEDS_AMOUNT; i++)
    {
        hsv_t hsv = {
            .h = phase + i * 360u / RING_LEDS_AMOUNT,
            .s = 100,
            .v = 100
        };
        rgb_t rgb = hsv_to_rgb(hsv);

        RingLedDisplay_Write_LedColor(i, rgb);
    }
}

static void rainbowFadeWriter(void* data)
{
    uint32_t* time = (uint32_t*) data;
    uint32_t phase = *time / 40;

    *time += RING_LED_UPDATE_TIME;

    hsv_t hsv = {
        .h = phase,
        .s = 100,
        .v = 100
    };
    rgb_t rgb = hsv_to_rgb(hsv);

    for (uint32_t i = 0u; i < RING_LEDS_AMOUNT; i++)
    {
        RingLedDisplay_Write_LedColor(i, rgb);
    }
}

static void init_spinningColor(void* data)
{
    spinning_color_data_t* sdata = (spinning_color_data_t*) data;
    sdata->time = 0u;
}

static void spinningColorWriter(void* data)
{
    spinning_color_data_t* sdata = (spinning_color_data_t*) data;
    uint32_t elapsed = sdata->time;
    sdata->time += RING_LED_UPDATE_TIME;

    const uint32_t tail_length = 6u;
    uint32_t n_leds = map_constrained(elapsed, 0, tail_length * 100, 0, tail_length);
    uint32_t start_led = (11u - tail_length) + (tail_length == n_leds ? elapsed / 100u : tail_length);

    hsv_t hsv = rgb_to_hsv(sdata->color);
    for (uint32_t i = 0u; i < RING_LEDS_AMOUNT; i++)
    {
        rgb_t rgb = LED_OFF;
        if (i < n_leds)
        {
            hsv.v = (uint8_t) map(i, 0, tail_length, 0, 100);
            rgb = hsv_to_rgb(hsv);
        }

        RingLedDisplay_Write_LedColor((start_led + i) % RING_LEDS_AMOUNT, rgb);
    }
}

static void init_breathing(void* data)
{
    breathing_data_t* bdata = (breathing_data_t*) data;
    bdata->time = 0u;
}

static void breathing(void* data)
{
    breathing_data_t* bdata = (breathing_data_t*) data;
    hsv_t color = rgb_to_hsv(bdata->color);

    uint32_t elapsed = bdata->time;
    bdata->time += RING_LED_UPDATE_TIME;

    float c = sinf(2.0f * (float)M_PI * elapsed / 10000.0f);
    color.v = map(c*c, 0, 1, 0, 100);

    rgb_t rgb = hsv_to_rgb(color);
    for (uint32_t i = 0u; i < RING_LEDS_AMOUNT; i++)
    {
        RingLedDisplay_Write_LedColor(i, rgb);
    }
}

static void siren(void* data)
{
    uint32_t* time_data = (uint32_t*) data;
    uint32_t elapsed = *time_data;
    *time_data += RING_LED_UPDATE_TIME;

    const uint32_t tail_length = 6u;
    uint32_t n_leds = map_constrained(elapsed, 0, tail_length * 75, 0, tail_length);
    uint32_t start_led = (11u - tail_length) + (tail_length == n_leds ? elapsed / 75u : tail_length);

    hsv_t hsv_r = rgb_to_hsv((rgb_t) LED_RED);
    hsv_t hsv_b = rgb_to_hsv((rgb_t) LED_BLUE);
    for (uint32_t i = 0u; i < RING_LEDS_AMOUNT/2; i++)
    {
        rgb_t rgb_r = LED_OFF;
        rgb_t rgb_b = LED_OFF;
        if (i < n_leds)
        {
            hsv_r.v = (uint8_t) map(i, 0, tail_length, 0, 100);
            rgb_r = hsv_to_rgb(hsv_r);

            hsv_b.v = (uint8_t) map(i, 0, tail_length, 0, 100);
            rgb_b = hsv_to_rgb(hsv_b);
        }

        RingLedDisplay_Write_LedColor((start_led + i) % RING_LEDS_AMOUNT, rgb_r);
        RingLedDisplay_Write_LedColor((start_led + i + 6) % RING_LEDS_AMOUNT, rgb_b);
    }
}

static void traffic_light(void* data)
{
    uint32_t* time_data = (uint32_t*) data;

    *time_data = (*time_data + RING_LED_UPDATE_TIME) % 8000u;

    rgb_t color;
    if (*time_data < 3000u)
    {
        color = (rgb_t) LED_RED;
    }
    else if (*time_data < 4000u)
    {
        color = (rgb_t) LED_ORANGE;
    }
    else if (*time_data < 7000u)
    {
        color = (rgb_t) LED_GREEN;
    }
    else
    {
        color = (rgb_t) LED_ORANGE;
    }

    for (uint32_t i = 0u; i < RING_LEDS_AMOUNT; i++)
    {
        RingLedDisplay_Write_LedColor(i, color);
    }
}


// Light up every other LED blinking.
static void bugIndicator(void* data)
{
    uint32_t* time_data = (uint32_t*) data;

    *time_data = (*time_data + RING_LED_UPDATE_TIME) % 400u;

    bool isOn = (*time_data / 200) % 2 == 0;

    if (isOn) {
        for (uint32_t i = 0u; i < RING_LEDS_AMOUNT; i++)
        {
            bool isEveryOtherLedOn = (i % 2) == 1;
            rgb_t color = isEveryOtherLedOn ? (rgb_t)LED_RED : (rgb_t)LED_OFF;
            RingLedDisplay_Write_LedColor(i, color );
        }
    } else {
        for (uint32_t i = 0u; i < RING_LEDS_AMOUNT; i++)
        {
            RingLedDisplay_Write_LedColor(i, (rgb_t)LED_ORANGE);
        }
    }
}


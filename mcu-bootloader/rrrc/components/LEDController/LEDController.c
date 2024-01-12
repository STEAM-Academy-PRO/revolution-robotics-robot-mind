/*
 * LEDController.c
 *
 * Created: 03/05/2019 10:31:19
 *  Author: Dániel Buga
 */

#include "LEDController.h"
#include "driver_init.h"
#include "../../include/color.h"
#include "../../utils/functions.h"

#include <stdint.h>
#include <string.h>

#define STATUS_LEDS_AMOUNT ((uint8_t) 4u)
#define RING_LEDS_AMOUNT   ((uint8_t) 12u)

#define LED_VAL_ZERO    ((uint8_t) 0xC0u)
#define LED_VAL_ONE     ((uint8_t) 0xFCu)
#define LED_VAL_RES     ((uint8_t) 0x00u)
#define LED_RESET_SIZE  ((size_t)    50u)

#define LED_BYTE_SIZE   8                   /* one LED control bit is coded as 8 MCU bits, so 1 byte -> 8 bytes */
#define LED_COLOR_SIZE  3 * LED_BYTE_SIZE   /* 24 LED bits in total */
#define LED_FRAME_SIZE  (LED_RESET_SIZE + (LED_COLOR_SIZE * (STATUS_LEDS_AMOUNT + RING_LEDS_AMOUNT)))

static bool ledsUpdating;

static uint8_t led_one;
static uint8_t led_zero;

static uint8_t frame_leds[LED_FRAME_SIZE];

static struct spi_m_dma_descriptor SPI_0;
static struct io_descriptor *io_descr;

//*********************************************************************************************
static void SPI_0_Init(void)
{
    hri_gclk_write_PCHCTRL_reg(GCLK, SERCOM4_GCLK_ID_CORE, CONF_GCLK_SERCOM4_CORE_SRC | (1 << GCLK_PCHCTRL_CHEN_Pos));
    hri_gclk_write_PCHCTRL_reg(GCLK, SERCOM4_GCLK_ID_SLOW, CONF_GCLK_SERCOM4_SLOW_SRC | (1 << GCLK_PCHCTRL_CHEN_Pos));
    hri_mclk_set_APBDMASK_SERCOM4_bit(MCLK);

    spi_m_dma_init(&SPI_0, SERCOM4);

    gpio_set_pin_level(WS2812pin, false);
    gpio_set_pin_direction(WS2812pin, GPIO_DIRECTION_OUT);
    gpio_set_pin_pull_mode(WS2812pin, GPIO_PULL_OFF);
    gpio_set_pin_function(WS2812pin, WS2812pin_function);
    //gpio_set_pin_drive(WS2812pin, GPIO_DRIVE_STRONG);
}

static inline uint8_t getLedBitPattern(uint8_t bitValue)
{
    return (bitValue == 0u) ? led_zero : led_one;
}

static inline void write_led_byte(uint32_t led_idx, uint32_t byte_idx, uint8_t byte_value)
{
    const uint32_t startIdx = LED_RESET_SIZE + 8u * (3u * led_idx + byte_idx); // TODO optimizer handles this?
    for (uint32_t i = 0u; i < 8u; i++)
    {
        frame_leds[startIdx + i] = getLedBitPattern(byte_value & (0x80u >> i));
    }
}

static inline void write_led_color(uint32_t led_idx, rgb_t color)
{
    /* brightness scaling */
    uint8_t max_brightness = LEDController_Read_MaxBrightness();
    rgb_t rgb_dimmed = rgb_change_brightness(color, max_brightness / 255.0f);

    write_led_byte(led_idx, 0u, rgb_dimmed.G);
    write_led_byte(led_idx, 1u, rgb_dimmed.R);
    write_led_byte(led_idx, 2u, rgb_dimmed.B);
}

static void update_frame(void)
{
    for (uint32_t i = 0u; i < STATUS_LEDS_AMOUNT; i++)
    {
        write_led_color(i, LEDController_Read_StatusLED(i));
    }

    for (uint32_t i = 0u; i < RING_LEDS_AMOUNT; i++)
    {
        write_led_color(STATUS_LEDS_AMOUNT + i, LEDController_Read_RingLED(i));
    }
}

static void send_frame(void)
{
    ledsUpdating = true;

    io_write(io_descr, frame_leds, ARRAY_SIZE(frame_leds));
    gpio_set_pin_function(WS2812pin, WS2812pin_function);
}

static void tx_complete_cb_SPI_0(struct _dma_resource *resource)
{
    (void) resource;
    ledsUpdating = false;
    bool inverted = (HARDWARE_VERSION != 0u);
    gpio_set_pin_level(WS2812pin, inverted ? true : false);
    gpio_set_pin_function(WS2812pin, GPIO_PIN_FUNCTION_OFF);
}

void LEDController_Run_OnInit(void)
{
    ledsUpdating = false;

    /* hw version 0 is for board without inverting FET */
    bool inverted = (HARDWARE_VERSION != 0u);
    uint8_t led_reset;
    if (inverted)
    {
        led_one = (uint8_t) ~LED_VAL_ONE;
        led_zero = (uint8_t) ~LED_VAL_ZERO;
        led_reset = (uint8_t) ~LED_VAL_RES;
    }
    else
    {
        led_one = LED_VAL_ONE;
        led_zero = LED_VAL_ZERO;
        led_reset = LED_VAL_RES;
    }

    memset(frame_leds, led_reset, sizeof(frame_leds));

    SPI_0_Init();

    spi_m_dma_get_io_descriptor(&SPI_0, &io_descr);
    spi_m_dma_register_callback(&SPI_0, SPI_M_DMA_CB_TX_DONE, &tx_complete_cb_SPI_0);
    spi_m_dma_enable(&SPI_0);
}

void LEDController_Run_Update(void)
{
    if (!ledsUpdating)
    {
        if (LEDController_Read_StatusLEDs_Changed() || LEDController_Read_RingLEDs_Changed())
        {
            update_frame();
            send_frame();
        }
    }
}

__attribute__((weak))
bool LEDController_Read_StatusLEDs_Changed(void)
{
    return true;
}

__attribute__((weak))
bool LEDController_Read_RingLEDs_Changed(void)
{
    return true;
}

__attribute__((weak))
rgb_t LEDController_Read_StatusLED(uint32_t led_idx)
{
    return (rgb_t) LED_MAGENTA;
}

__attribute__((weak))
rgb_t LEDController_Read_RingLED(uint32_t led_idx)
{
    return (rgb_t){0, 0, 0};
}

__attribute__((weak))
uint8_t LEDController_Read_MaxBrightness(void)
{
    return 32u;
}

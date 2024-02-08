#ifndef ATMEL_START_PINS_H_INCLUDED
#define ATMEL_START_PINS_H_INCLUDED

#include <stdio.h>
#include <stdint.h>

typedef uint8_t gpio_pin_t;

#include "libraries/fast_gpio/fast_gpio.h"

#define GPIO_PIN_FUNCTION_A 0
#define GPIO_PIN_FUNCTION_B 1
#define GPIO_PIN_FUNCTION_C 2
#define GPIO_PIN_FUNCTION_D 3
#define GPIO_PIN_FUNCTION_E 4
#define GPIO_PIN_FUNCTION_F 5
#define GPIO_PIN_FUNCTION_G 6
#define GPIO_PIN_FUNCTION_H 7
#define GPIO_PIN_FUNCTION_I 8
#define GPIO_PIN_FUNCTION_J 9
#define GPIO_PIN_FUNCTION_K 10
#define GPIO_PIN_FUNCTION_L 11
#define GPIO_PIN_FUNCTION_M 12
#define GPIO_PIN_FUNCTION_N 13

#define PA00 GPIO(GPIO_PORTA, 0)
#define PA01 GPIO(GPIO_PORTA, 1)
#define PA02 GPIO(GPIO_PORTA, 2)
#define PA03 GPIO(GPIO_PORTA, 3)
#define PA04 GPIO(GPIO_PORTA, 4)
#define PA05 GPIO(GPIO_PORTA, 5)
#define PA06 GPIO(GPIO_PORTA, 6)
#define PA07 GPIO(GPIO_PORTA, 7)
#define PA08 GPIO(GPIO_PORTA, 8)
#define PA09 GPIO(GPIO_PORTA, 9)
#define PA10 GPIO(GPIO_PORTA, 10)
#define PA11 GPIO(GPIO_PORTA, 11)
#define PA12 GPIO(GPIO_PORTA, 12)
#define PA13 GPIO(GPIO_PORTA, 13)
#define PA14 GPIO(GPIO_PORTA, 14)
#define PA15 GPIO(GPIO_PORTA, 15)
#define PA16 GPIO(GPIO_PORTA, 16)
#define PA17 GPIO(GPIO_PORTA, 17)
#define PA18 GPIO(GPIO_PORTA, 18)
#define PA19 GPIO(GPIO_PORTA, 19)
#define PA20 GPIO(GPIO_PORTA, 20)
#define PA21 GPIO(GPIO_PORTA, 21)
#define PA22 GPIO(GPIO_PORTA, 22)
#define PA23 GPIO(GPIO_PORTA, 23)
#define PA24 GPIO(GPIO_PORTA, 24)
#define PA25 GPIO(GPIO_PORTA, 25)
#define PA26 GPIO(GPIO_PORTA, 26)
#define PA27 GPIO(GPIO_PORTA, 27)
#define PA28 GPIO(GPIO_PORTA, 28)
#define PA29 GPIO(GPIO_PORTA, 29)
#define PA30 GPIO(GPIO_PORTA, 30)
#define PA31 GPIO(GPIO_PORTA, 31)

#define PB00 GPIO(GPIO_PORTB, 0)
#define PB01 GPIO(GPIO_PORTB, 1)
#define PB02 GPIO(GPIO_PORTB, 2)
#define PB03 GPIO(GPIO_PORTB, 3)
#define PB04 GPIO(GPIO_PORTB, 4)
#define PB05 GPIO(GPIO_PORTB, 5)
#define PB06 GPIO(GPIO_PORTB, 6)
#define PB07 GPIO(GPIO_PORTB, 7)
#define PB08 GPIO(GPIO_PORTB, 8)
#define PB09 GPIO(GPIO_PORTB, 9)
#define PB10 GPIO(GPIO_PORTB, 10)
#define PB11 GPIO(GPIO_PORTB, 11)
#define PB12 GPIO(GPIO_PORTB, 12)
#define PB13 GPIO(GPIO_PORTB, 13)
#define PB14 GPIO(GPIO_PORTB, 14)
#define PB15 GPIO(GPIO_PORTB, 15)
#define PB16 GPIO(GPIO_PORTB, 16)
#define PB17 GPIO(GPIO_PORTB, 17)
#define PB18 GPIO(GPIO_PORTB, 18)
#define PB19 GPIO(GPIO_PORTB, 19)
#define PB20 GPIO(GPIO_PORTB, 20)
#define PB21 GPIO(GPIO_PORTB, 21)
#define PB22 GPIO(GPIO_PORTB, 22)
#define PB23 GPIO(GPIO_PORTB, 23)
#define PB24 GPIO(GPIO_PORTB, 24)
#define PB25 GPIO(GPIO_PORTB, 25)
#define PB26 GPIO(GPIO_PORTB, 26)
#define PB27 GPIO(GPIO_PORTB, 27)
#define PB28 GPIO(GPIO_PORTB, 28)
#define PB29 GPIO(GPIO_PORTB, 29)
#define PB30 GPIO(GPIO_PORTB, 30)
#define PB31 GPIO(GPIO_PORTB, 31)

#define PC00 GPIO(GPIO_PORTC, 0)
#define PC01 GPIO(GPIO_PORTC, 1)
#define PC02 GPIO(GPIO_PORTC, 2)
#define PC03 GPIO(GPIO_PORTC, 3)
#define PC04 GPIO(GPIO_PORTC, 4)
#define PC05 GPIO(GPIO_PORTC, 5)
#define PC06 GPIO(GPIO_PORTC, 6)
#define PC07 GPIO(GPIO_PORTC, 7)
#define PC08 GPIO(GPIO_PORTC, 8)
#define PC09 GPIO(GPIO_PORTC, 9)
#define PC10 GPIO(GPIO_PORTC, 10)
#define PC11 GPIO(GPIO_PORTC, 11)
#define PC12 GPIO(GPIO_PORTC, 12)
#define PC13 GPIO(GPIO_PORTC, 13)
#define PC14 GPIO(GPIO_PORTC, 14)
#define PC15 GPIO(GPIO_PORTC, 15)
#define PC16 GPIO(GPIO_PORTC, 16)
#define PC17 GPIO(GPIO_PORTC, 17)
#define PC18 GPIO(GPIO_PORTC, 18)
#define PC19 GPIO(GPIO_PORTC, 19)
#define PC20 GPIO(GPIO_PORTC, 20)
#define PC21 GPIO(GPIO_PORTC, 21)
#define PC22 GPIO(GPIO_PORTC, 22)
#define PC23 GPIO(GPIO_PORTC, 23)
#define PC24 GPIO(GPIO_PORTC, 24)
#define PC25 GPIO(GPIO_PORTC, 25)
#define PC26 GPIO(GPIO_PORTC, 26)
#define PC27 GPIO(GPIO_PORTC, 27)
#define PC28 GPIO(GPIO_PORTC, 28)
#define PC29 GPIO(GPIO_PORTC, 29)
#define PC30 GPIO(GPIO_PORTC, 30)
#define PC31 GPIO(GPIO_PORTC, 31)

#define PD00 GPIO(GPIO_PORTD, 0)
#define PD01 GPIO(GPIO_PORTD, 1)
#define PD02 GPIO(GPIO_PORTD, 2)
#define PD03 GPIO(GPIO_PORTD, 3)
#define PD04 GPIO(GPIO_PORTD, 4)
#define PD05 GPIO(GPIO_PORTD, 5)
#define PD06 GPIO(GPIO_PORTD, 6)
#define PD07 GPIO(GPIO_PORTD, 7)
#define PD08 GPIO(GPIO_PORTD, 8)
#define PD09 GPIO(GPIO_PORTD, 9)
#define PD10 GPIO(GPIO_PORTD, 10)
#define PD11 GPIO(GPIO_PORTD, 11)
#define PD12 GPIO(GPIO_PORTD, 12)
#define PD13 GPIO(GPIO_PORTD, 13)
#define PD14 GPIO(GPIO_PORTD, 14)
#define PD15 GPIO(GPIO_PORTD, 15)
#define PD16 GPIO(GPIO_PORTD, 16)
#define PD17 GPIO(GPIO_PORTD, 17)
#define PD18 GPIO(GPIO_PORTD, 18)
#define PD19 GPIO(GPIO_PORTD, 19)
#define PD20 GPIO(GPIO_PORTD, 20)
#define PD21 GPIO(GPIO_PORTD, 21)
#define PD22 GPIO(GPIO_PORTD, 22)
#define PD23 GPIO(GPIO_PORTD, 23)
#define PD24 GPIO(GPIO_PORTD, 24)
#define PD25 GPIO(GPIO_PORTD, 25)
#define PD26 GPIO(GPIO_PORTD, 26)
#define PD27 GPIO(GPIO_PORTD, 27)
#define PD28 GPIO(GPIO_PORTD, 28)
#define PD29 GPIO(GPIO_PORTD, 29)
#define PD30 GPIO(GPIO_PORTD, 30)
#define PD31 GPIO(GPIO_PORTD, 31)

#define PE00 GPIO(GPIO_PORTE, 0)
#define PE01 GPIO(GPIO_PORTE, 1)
#define PE02 GPIO(GPIO_PORTE, 2)
#define PE03 GPIO(GPIO_PORTE, 3)
#define PE04 GPIO(GPIO_PORTE, 4)
#define PE05 GPIO(GPIO_PORTE, 5)
#define PE06 GPIO(GPIO_PORTE, 6)
#define PE07 GPIO(GPIO_PORTE, 7)
#define PE08 GPIO(GPIO_PORTE, 8)
#define PE09 GPIO(GPIO_PORTE, 9)
#define PE10 GPIO(GPIO_PORTE, 10)
#define PE11 GPIO(GPIO_PORTE, 11)
#define PE12 GPIO(GPIO_PORTE, 12)
#define PE13 GPIO(GPIO_PORTE, 13)
#define PE14 GPIO(GPIO_PORTE, 14)
#define PE15 GPIO(GPIO_PORTE, 15)
#define PE16 GPIO(GPIO_PORTE, 16)
#define PE17 GPIO(GPIO_PORTE, 17)
#define PE18 GPIO(GPIO_PORTE, 18)
#define PE19 GPIO(GPIO_PORTE, 19)
#define PE20 GPIO(GPIO_PORTE, 20)
#define PE21 GPIO(GPIO_PORTE, 21)
#define PE22 GPIO(GPIO_PORTE, 22)
#define PE23 GPIO(GPIO_PORTE, 23)
#define PE24 GPIO(GPIO_PORTE, 24)
#define PE25 GPIO(GPIO_PORTE, 25)
#define PE26 GPIO(GPIO_PORTE, 26)
#define PE27 GPIO(GPIO_PORTE, 27)
#define PE28 GPIO(GPIO_PORTE, 28)
#define PE29 GPIO(GPIO_PORTE, 29)
#define PE30 GPIO(GPIO_PORTE, 30)
#define PE31 GPIO(GPIO_PORTE, 31)

/* Hardware version v4.5 */

/* ========== Motor ports ========== */

/* Motor port 0 */
#define M0_GREEN_LED        PB22
#define M0_ISEN_AIN         PB04
#define M0_ISEN_ADC         1
#define M0_ISEN_CH          6
#define M0_ENC_A            FAST_FROM_GPIO(PB25)
#define M0_ENC_B            FAST_FROM_GPIO(PB24)

/* Motor port 1 */
#define M1_GREEN_LED        PC24
#define M1_ISEN_AIN         PB03
#define M1_ISEN_ADC         0
#define M1_ISEN_CH          15
#define M1_ENC_A            FAST_FROM_GPIO(PB27)
#define M1_ENC_B            FAST_FROM_GPIO(PA20)

/* Motor port 2 */
#define M2_GREEN_LED        PC26
#define M2_ISEN_AIN         PC00
#define M2_ISEN_ADC         1
#define M2_ISEN_CH          10
#define M2_ENC_A            FAST_FROM_GPIO(PA02)
#define M2_ENC_B            FAST_FROM_GPIO(PA21)

/* Motor port 3 */
#define M3_GREEN_LED        PC12
#define M3_ISEN_AIN         PA11
#define M3_ISEN_ADC         0
#define M3_ISEN_CH          11
#define M3_ENC_A            FAST_PIN(GPIO_PORTB, 17)
#define M3_ENC_B            FAST_PIN(GPIO_PORTB,  7)

/* Motor port 4 */
#define M4_GREEN_LED        PD12
#define M4_ISEN_AIN         PA10
#define M4_ISEN_ADC         0
#define M4_ISEN_CH          10
#define M4_ENC_A            FAST_PIN(GPIO_PORTB, 15)
#define M4_ENC_B            FAST_PIN(GPIO_PORTC, 10)

/* Motor port 5 */
#define M5_GREEN_LED        PC14
#define M5_ISEN_AIN         PC02
#define M5_ISEN_ADC         1
#define M5_ISEN_CH          4
#define M5_ENC_A            FAST_PIN(GPIO_PORTB, 16)
#define M5_ENC_B            FAST_PIN(GPIO_PORTB, 14)

/* Motor drivers */
#define MOTOR_DRIVER_0_EN       PB20
#define MOTOR_DRIVER_0_FAULT    PB23

#define MOTOR_DRIVER_0_CH_A_PWM_TIMER        4
#define MOTOR_DRIVER_0_CH_A_PWM0_PIN         PB08
#define MOTOR_DRIVER_0_CH_A_PWM0_CH          0
#define MOTOR_DRIVER_0_CH_A_PWM1_PIN         PB09
#define MOTOR_DRIVER_0_CH_A_PWM1_CH          1
#define MOTOR_DRIVER_0_CH_A_ISEN             M1_ISEN_AIN

#define MOTOR_DRIVER_0_CH_B_PWM_TIMER        2
#define MOTOR_DRIVER_0_CH_B_PWM0_PIN         PA00
#define MOTOR_DRIVER_0_CH_B_PWM0_CH          0
#define MOTOR_DRIVER_0_CH_B_PWM1_PIN         PA01
#define MOTOR_DRIVER_0_CH_B_PWM1_CH          1
#define MOTOR_DRIVER_0_CH_B_ISEN             M2_ISEN_AIN

#define MOTOR_DRIVER_1_EN       PD01
#define MOTOR_DRIVER_1_FAULT    PC13

#define MOTOR_DRIVER_1_CH_A_PWM_TIMER        0
#define MOTOR_DRIVER_1_CH_A_PWM0_PIN         PA04
#define MOTOR_DRIVER_1_CH_A_PWM0_CH          0
#define MOTOR_DRIVER_1_CH_A_PWM1_PIN         PA05
#define MOTOR_DRIVER_1_CH_A_PWM1_CH          1
#define MOTOR_DRIVER_1_CH_A_ISEN             M0_ISEN_AIN

#define MOTOR_DRIVER_1_CH_B_PWM_TIMER        3
#define MOTOR_DRIVER_1_CH_B_PWM0_PIN         PA14
#define MOTOR_DRIVER_1_CH_B_PWM0_CH          0
#define MOTOR_DRIVER_1_CH_B_PWM1_PIN         PA15
#define MOTOR_DRIVER_1_CH_B_PWM1_CH          1
#define MOTOR_DRIVER_1_CH_B_ISEN             M5_ISEN_AIN

#define MOTOR_DRIVER_2_EN       PA18
#define MOTOR_DRIVER_2_FAULT    PB13

#define MOTOR_DRIVER_2_CH_A_PWM_TIMER        1
#define MOTOR_DRIVER_2_CH_A_PWM0_PIN         PA06
#define MOTOR_DRIVER_2_CH_A_PWM0_CH          0
#define MOTOR_DRIVER_2_CH_A_PWM1_PIN         PA07
#define MOTOR_DRIVER_2_CH_A_PWM1_CH          1
#define MOTOR_DRIVER_2_CH_A_ISEN             M3_ISEN_AIN

#define MOTOR_DRIVER_2_CH_B_PWM_TIMER        5
#define MOTOR_DRIVER_2_CH_B_PWM0_PIN         PB10
#define MOTOR_DRIVER_2_CH_B_PWM0_CH          0
#define MOTOR_DRIVER_2_CH_B_PWM1_PIN         PB11
#define MOTOR_DRIVER_2_CH_B_PWM1_CH          1
#define MOTOR_DRIVER_2_CH_B_ISEN             M4_ISEN_AIN

/* ========== Sensor ports ========== */
/* Sensor port 0 */
#define S0_IOVCC        PC04
#define S0_AIN          PB02
#define S0_ADC_PER      0
#define S0_ADC_CH       14
#define S0_GPIO_OUT     PC27
#define S0_GPIO_IN      PA27
#define S0_LED_GREEN    PB21
#define S0_LED_YELLOW   PC25

#define SENSOR_0_SERCOM          SERCOM3
#define SENSOR_0_SDApin          PA22
#define SENSOR_0_SDApin_function GPIO_PIN_FUNCTION_C
#define SENSOR_0_SCLpin          PA23
#define SENSOR_0_SCLpin_function GPIO_PIN_FUNCTION_C

/* Sensor port 1 */
#define S1_IOVCC        PC05
#define S1_AIN          PC01
#define S1_ADC_PER      1
#define S1_ADC_CH       11
#define S1_GPIO_OUT     PB19
#define S1_GPIO_IN      PA03
#define S1_LED_GREEN    PC17
#define S1_LED_YELLOW   PD00

#define SENSOR_1_SERCOM          SERCOM1
#define SENSOR_1_SDApin          PA16
#define SENSOR_1_SDApin_function GPIO_PIN_FUNCTION_C
#define SENSOR_1_SCLpin          PA17
#define SENSOR_1_SCLpin_function GPIO_PIN_FUNCTION_C

/* Sensor port 2 */
#define S2_IOVCC        PC06
#define S2_AIN          PC03
#define S2_ADC_PER      1
#define S2_ADC_CH       5
#define S2_GPIO_OUT     PC16
#define S2_GPIO_IN      PB12
#define S2_LED_GREEN    PC15
#define S2_LED_YELLOW   PA19

#define SENSOR_2_SERCOM          SERCOM0
#define SENSOR_2_SDApin          PA08
#define SENSOR_2_SDApin_function GPIO_PIN_FUNCTION_C
#define SENSOR_2_SCLpin          PA09
#define SENSOR_2_SCLpin_function GPIO_PIN_FUNCTION_C

/* Sensor port 3 */
#define S3_IOVCC        PC07
#define S3_AIN          PB05
#define S3_ADC_PER      1
#define S3_ADC_CH       7
#define S3_GPIO_OUT     PD11
#define S3_GPIO_IN      PB06
#define S3_LED_GREEN    PD10
#define S3_LED_YELLOW   PC11

#define SENSOR_3_SERCOM          SERCOM6
#define SENSOR_3_SDApin          PD09
#define SENSOR_3_SDApin_function GPIO_PIN_FUNCTION_D
#define SENSOR_3_SCLpin          PD08
#define SENSOR_3_SCLpin_function GPIO_PIN_FUNCTION_D

// PAD[0] Digital I/O SDA
// PAD[1] Digital I/O SCL
// PAD[2] Digital I/O SDA_OUT (4-wire operation)
// PAD[3] Digital I/O SCL_OUT (4-wire operation)

/* Misc */
/* SERCOM2!! (RPi) */
#define I2C4_SERCOM          SERCOM2
#define I2C4_SDApin          PA12
#define I2C4_SDApin_function GPIO_PIN_FUNCTION_C
#define I2C4_SCLpin          PA13
#define I2C4_SCLpin_function GPIO_PIN_FUNCTION_C

#define RPi_I2C_sda          I2C4_SDApin
#define RPi_I2C_scl          I2C4_SCLpin

#define WS2812spi           SERCOM4
#define WS2812pin           PB29
#define WS2812pin_function  GPIO_PIN_FUNCTION_D

#define IMU_SERCOM            SERCOM5
#define IMU_MISO_pin          PB01
#define IMU_MISO_pin_function PINMUX_PB01D_SERCOM5_PAD3
#define IMU_MOSI_pin          PB31
#define IMU_MOSI_pin_function PINMUX_PB31D_SERCOM5_PAD0
#define IMU_SCLK_pin          PB30
#define IMU_SCLK_pin_function PINMUX_PB30D_SERCOM5_PAD1
#define IMU_CS_pin            PB00
#define IMU_CS_pin_function   GPIO_PIN_FUNCTION_OFF
#define IMU_INT1_pin          PB26
#define IMU_INT2_pin          PB28

#define CHARGER_STBY        PC21
#define CHARGER_STAT        PC23

#define SM_MOT_VOLTAGE          PC30
#define SM_BAT_VOLTAGE          PC31

#define ADC_CH_MOT_VOLTAGE      12
#define ADC_CH_BAT_VOLTAGE      13

#define ADC_CHN_INT_GND       0x18

#endif // ATMEL_START_PINS_H_INCLUDED

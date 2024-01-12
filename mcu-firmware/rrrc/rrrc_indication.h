/*
 * rrrc_indication.h
 *
 * Created: 10-Mar-19 01:42:29
 *  Author: vmyakovlev
 */ 


#ifndef RRRC_INDICATION_H_
#define RRRC_INDICATION_H_

#include <stdint.h>
#include "utils/color.h"

#define STATUS_LEDS_AMOUNT 4
#define RING_LEDS_AMOUNT 12

// /* some RGB color definitions                                                 */
// #define Black           0x0000      /*   0,   0,   0 */
// #define Navy            0x000F      /*   0,   0, 128 */
// #define DarkGreen       0x03E0      /*   0, 128,   0 */
// #define DarkCyan        0x03EF      /*   0, 128, 128 */
// #define Maroon          0x7800      /* 128,   0,   0 */
// #define Purple          0x780F      /* 128,   0, 128 */
// #define Olive           0x7BE0      /* 128, 128,   0 */
// #define LightGrey       0xC618      /* 192, 192, 192 */
// #define DarkGrey        0x7BEF      /* 128, 128, 128 */
// #define Blue            0x001F      /*   0,   0, 255 */
// #define Green           0x07E0      /*   0, 255,   0 */
// #define Cyan            0x07FF      /*   0, 255, 255 */
// #define Red             0xF800      /* 255,   0,   0 */
// #define Magenta         0xF81F      /* 255,   0, 255 */
// #define Yellow          0xFFE0      /* 255, 255,   0 */
// #define White           0xFFFF      /* 255, 255, 255 */
// #define Orange          0xFD20      /* 255, 165,   0 */
// #define GreenYellow     0xAFE5      /* 173, 255,  47 */
// #define Pink                        0xF81F

#define LED_BRIGHT  0xFF

#define LED_RED     { LED_BRIGHT,     0x00,           0x00           }
#define LED_GREEN   { 0x00,           LED_BRIGHT,     0x00           }
#define LED_BLUE    { 0x00,           0x00,           LED_BRIGHT     }
#define LED_YELLOW  { LED_BRIGHT,     LED_BRIGHT,     0x00           }
#define LED_ORANGE  { LED_BRIGHT,     LED_BRIGHT / 3, 0x00           }
#define LED_CYAN    { 0x00,           LED_BRIGHT,     LED_BRIGHT     }
#define LED_MAGENTA { LED_BRIGHT,     0x00,           LED_BRIGHT     }
#define LED_WHITE   { LED_BRIGHT / 4, LED_BRIGHT / 4, LED_BRIGHT / 4 }
#define LED_OFF     { 0x00,           0x00,           0x00           }

#define LED_HSV_CYAN    0, 100, 100

#endif /* RRRC_INDICATION_H_ */
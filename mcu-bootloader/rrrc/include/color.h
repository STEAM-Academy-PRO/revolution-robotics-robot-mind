/*
 * color.h
 *
 * Created: 2019. 06. 27. 10:01:38
 *  Author: bugad
 */ 


#ifndef LED_COLOR_H_
#define LED_COLOR_H_

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

#endif /* LED_COLOR_H_ */

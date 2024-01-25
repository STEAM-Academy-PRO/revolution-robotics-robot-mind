#ifndef COMPONENT_LEDCONTROLLER_H_
#define COMPONENT_LEDCONTROLLER_H_

#include "../../utils/color.h"

#include <stdbool.h>

void LEDController_Run_OnInit(void);
void LEDController_Run_Update(void);
uint8_t LEDController_Read_MaxBrightness(void);

bool LEDController_Read_StatusLEDs_Changed(void);
bool LEDController_Read_RingLEDs_Changed(void);

rgb_t LEDController_Read_StatusLED(uint32_t led_idx);
rgb_t LEDController_Read_RingLED(uint32_t led_idx);

#endif /* LEDCONTROLLER_H_ */

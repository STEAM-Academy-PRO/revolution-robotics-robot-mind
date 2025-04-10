#ifndef COMPONENT_LED_CONTROLLER_H_
#define COMPONENT_LED_CONTROLLER_H_

#ifndef COMPONENT_TYPES_LED_CONTROLLER_H_
#define COMPONENT_TYPES_LED_CONTROLLER_H_

#include "CommonLibraries/color.h"
#include <stdbool.h>
#include <stdint.h>


#endif /* COMPONENT_TYPES_LED_CONTROLLER_H_ */

/* Begin User Code Section: Declarations */

/* End User Code Section: Declarations */

void LEDController_Run_OnInit(void);
void LEDController_Run_Update(void);
uint8_t LEDController_Read_MaxBrightness(void);
rgb_t LEDController_Read_RingLED(uint32_t index);
bool LEDController_Read_RingLEDs_Changed(void);
rgb_t LEDController_Read_StatusLED(uint32_t index);
bool LEDController_Read_StatusLEDs_Changed(void);

#endif /* COMPONENT_LED_CONTROLLER_H_ */

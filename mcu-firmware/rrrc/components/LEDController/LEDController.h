#ifndef COMPONENT_LED_CONTROLLER_H_
#define COMPONENT_LED_CONTROLLER_H_

#ifndef COMPONENT_TYPES_LED_CONTROLLER_H_
#define COMPONENT_TYPES_LED_CONTROLLER_H_

#include "libraries/color.h"
#include <stdint.h>


#endif /* COMPONENT_TYPES_LED_CONTROLLER_H_ */

/* Begin User Code Section: Declarations */

/* End User Code Section: Declarations */

void LEDController_Run_OnInit(void);
void LEDController_Run_Update(void);
rgb_t LEDController_Read_Colors(uint32_t index);
uint8_t LEDController_Read_MaxBrightness(void);

#endif /* COMPONENT_LED_CONTROLLER_H_ */

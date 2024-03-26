#ifndef COMPONENT_LED_CONTROLLER__BOOTLOADER_H_
#define COMPONENT_LED_CONTROLLER__BOOTLOADER_H_

#ifndef COMPONENT_TYPES_LED_CONTROLLER__BOOTLOADER_H_
#define COMPONENT_TYPES_LED_CONTROLLER__BOOTLOADER_H_

#include "utils/color.h"
#include <stdbool.h>
#include <stdint.h>


#endif /* COMPONENT_TYPES_LED_CONTROLLER__BOOTLOADER_H_ */

/* Begin User Code Section: Declarations */
/*
FIXME: CGlue runtime generator does not include stdbool.h if no declared type uses it.
The generator should not ignore the types used by port definitions.
*/
#include <stdbool.h>
/* End User Code Section: Declarations */

void LEDController_Bootloader_Run_OnInit(void);
void LEDController_Bootloader_Run_Update(void);
uint8_t LEDController_Bootloader_Read_MaxBrightness(void);
rgb_t LEDController_Bootloader_Read_RingLED(uint32_t index);
bool LEDController_Bootloader_Read_RingLEDs_Changed(void);
rgb_t LEDController_Bootloader_Read_StatusLED(uint32_t index);
bool LEDController_Bootloader_Read_StatusLEDs_Changed(void);

#endif /* COMPONENT_LED_CONTROLLER__BOOTLOADER_H_ */

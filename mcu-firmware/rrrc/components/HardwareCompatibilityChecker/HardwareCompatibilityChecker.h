#ifndef COMPONENT_HARDWARE_COMPATIBILITY_CHECKER_H_
#define COMPONENT_HARDWARE_COMPATIBILITY_CHECKER_H_

#ifndef COMPONENT_TYPES_HARDWARE_COMPATIBILITY_CHECKER_H_
#define COMPONENT_TYPES_HARDWARE_COMPATIBILITY_CHECKER_H_

#include <stdint.h>


#endif /* COMPONENT_TYPES_HARDWARE_COMPATIBILITY_CHECKER_H_ */

void HardwareCompatibilityChecker_Run_OnInit(void);
void HardwareCompatibilityChecker_RaiseEvent_OnIncompatibleHardware(void);
uint32_t HardwareCompatibilityChecker_Read_HardwareVersion(void);

#endif /* COMPONENT_HARDWARE_COMPATIBILITY_CHECKER_H_ */

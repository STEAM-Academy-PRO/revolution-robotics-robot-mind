#include "ProjectConfiguration.h"
#include "utils.h"
#include "utils_assert.h"

/* Begin User Code Section: Declarations */

/* End User Code Section: Declarations */

uint8_t ProjectConfiguration_Constant_DeviceAddress(void)
{
    /* Begin User Code Section: DeviceAddress:constant Start */

    /* End User Code Section: DeviceAddress:constant Start */
    /* Begin User Code Section: DeviceAddress:constant End */

    /* End User Code Section: DeviceAddress:constant End */
    return 0x2D;
}

uint32_t ProjectConfiguration_Constant_ExpectedStartupTime(void)
{
    /* Begin User Code Section: ExpectedStartupTime:constant Start */

    /* End User Code Section: ExpectedStartupTime:constant Start */
    /* Begin User Code Section: ExpectedStartupTime:constant End */

    /* End User Code Section: ExpectedStartupTime:constant End */
    return 15000;
}

uint32_t ProjectConfiguration_Constant_ExpectedUpdateTime(void)
{
    /* Begin User Code Section: ExpectedUpdateTime:constant Start */

    /* End User Code Section: ExpectedUpdateTime:constant Start */
    /* Begin User Code Section: ExpectedUpdateTime:constant End */

    /* End User Code Section: ExpectedUpdateTime:constant End */
    return 300000;
}

void ProjectConfiguration_Constant_MainBatteryParameters(BatteryConfiguration_t* value)
{
    ASSERT(value != NULL);
    /* Begin User Code Section: MainBatteryParameters:constant Start */

    /* End User Code Section: MainBatteryParameters:constant Start */
    *value = (BatteryConfiguration_t) {
        .detectionVoltage = 2000.0f,
        .minVoltage       = 3300.0f,
        .maxVoltage       = 4100.0f
    };
    /* Begin User Code Section: MainBatteryParameters:constant End */

    /* End User Code Section: MainBatteryParameters:constant End */
}

uint32_t ProjectConfiguration_Constant_MaxStartupTime(void)
{
    /* Begin User Code Section: MaxStartupTime:constant Start */

    /* End User Code Section: MaxStartupTime:constant Start */
    /* Begin User Code Section: MaxStartupTime:constant End */

    /* End User Code Section: MaxStartupTime:constant End */
    return 60000;
}

void ProjectConfiguration_Constant_MotorBatteryParameters(BatteryConfiguration_t* value)
{
    ASSERT(value != NULL);
    /* Begin User Code Section: MotorBatteryParameters:constant Start */

    /* End User Code Section: MotorBatteryParameters:constant Start */
    *value = (BatteryConfiguration_t) {
        .detectionVoltage = 4000.0f,
        .minVoltage       = 5400.0f,
        .maxVoltage       = 7000.0f
    };
    /* Begin User Code Section: MotorBatteryParameters:constant End */

    /* End User Code Section: MotorBatteryParameters:constant End */
}

void ProjectConfiguration_Constant_MotorDeratingParameters(MotorDeratingParameters_t* value)
{
    ASSERT(value != NULL);
    /* Begin User Code Section: MotorDeratingParameters:constant Start */

    /* End User Code Section: MotorDeratingParameters:constant Start */
    *value = (MotorDeratingParameters_t) {
        .MaxSafeTemperature    = 70.0f,
        .MaxAllowedTemperature = 130.0f
    };
    /* Begin User Code Section: MotorDeratingParameters:constant End */

    /* End User Code Section: MotorDeratingParameters:constant End */
}

void ProjectConfiguration_Constant_MotorPortGpios(uint32_t index, MotorPortGpios_t* value)
{
    ASSERT(index < 6);
    ASSERT(value != NULL);
    /* Begin User Code Section: MotorPortGpios:constant Start */

    /* End User Code Section: MotorPortGpios:constant Start */
    static const MotorPortGpios_t constant[6] = {
        (MotorPortGpios_t) {
            .led  = M5_GREEN_LED,
            .enc0 = M5_ENC_A,
            .enc1 = M5_ENC_B
        },
        (MotorPortGpios_t) {
            .led  = M4_GREEN_LED,
            .enc0 = M4_ENC_A,
            .enc1 = M4_ENC_B
        },
        (MotorPortGpios_t) {
            .led  = M3_GREEN_LED,
            .enc0 = M3_ENC_A,
            .enc1 = M3_ENC_B
        },
        (MotorPortGpios_t) {
            .led  = M0_GREEN_LED,
            .enc0 = M0_ENC_A,
            .enc1 = M0_ENC_B
        },
        (MotorPortGpios_t) {
            .led  = M1_GREEN_LED,
            .enc0 = M1_ENC_A,
            .enc1 = M1_ENC_B
        },
        (MotorPortGpios_t) {
            .led  = M2_GREEN_LED,
            .enc0 = M2_ENC_A,
            .enc1 = M2_ENC_B
        }
    };
    *value = constant[index];
    /* Begin User Code Section: MotorPortGpios:constant End */

    /* End User Code Section: MotorPortGpios:constant End */
}

void ProjectConfiguration_Constant_MotorThermalParameters(MotorThermalParameters_t* value)
{
    ASSERT(value != NULL);
    /* Begin User Code Section: MotorThermalParameters:constant Start */

    /* End User Code Section: MotorThermalParameters:constant Start */
    *value = (MotorThermalParameters_t) {
        .resistance    = 3.5f,
        .coeff_cooling = 0.02f,
        .coeff_heating = 0.2f
    };
    /* Begin User Code Section: MotorThermalParameters:constant End */

    /* End User Code Section: MotorThermalParameters:constant End */
}

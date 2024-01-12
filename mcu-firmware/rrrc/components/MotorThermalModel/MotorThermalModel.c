#include "MotorThermalModel.h"
#include "utils.h"
#include "utils_assert.h"

/* Begin User Code Section: Declarations */
typedef struct {
    float temperature;
} MotorThermalModel_t;

static MotorThermalModel_t models[6] = {};
/* End User Code Section: Declarations */

void MotorThermalModel_Run_OnInit(void)
{
    /* Begin User Code Section: OnInit:run Start */
    for (uint32_t i = 0u; i < ARRAY_SIZE(models); i++)
    {
        models[i].temperature = MotorThermalModel_Read_AmbientTemperature();
    }
    /* End User Code Section: OnInit:run Start */
    /* Begin User Code Section: OnInit:run End */

    /* End User Code Section: OnInit:run End */
}

void MotorThermalModel_Run_OnUpdate(void)
{
    /* Begin User Code Section: OnUpdate:run Start */
    MotorThermalParameters_t params;
    MotorThermalModel_Read_ThermalParameters(&params);

    Temperature_t ambient = MotorThermalModel_Read_AmbientTemperature();

    for (uint32_t i = 0u; i < ARRAY_SIZE(models); i++)
    {
        float current = MotorThermalModel_Read_MotorCurrent(i);
        float power = current * current * params.resistance;

        float cooling = params.coeff_cooling * (models[i].temperature - ambient);
        float heating = params.coeff_heating * power;

        models[i].temperature += heating - cooling;
        MotorThermalModel_Write_Temperature(i, models[i].temperature);
    }
    /* End User Code Section: OnUpdate:run Start */
    /* Begin User Code Section: OnUpdate:run End */

    /* End User Code Section: OnUpdate:run End */
}

__attribute__((weak))
void MotorThermalModel_Write_Temperature(uint32_t index, Temperature_t value)
{
    (void) value;
    ASSERT(index < 6);
    /* Begin User Code Section: Temperature:write Start */

    /* End User Code Section: Temperature:write Start */
    /* Begin User Code Section: Temperature:write End */

    /* End User Code Section: Temperature:write End */
}

__attribute__((weak))
Temperature_t MotorThermalModel_Read_AmbientTemperature(void)
{
    /* Begin User Code Section: AmbientTemperature:read Start */

    /* End User Code Section: AmbientTemperature:read Start */
    /* Begin User Code Section: AmbientTemperature:read End */

    /* End User Code Section: AmbientTemperature:read End */
    return (Temperature_t) 20.0f;
}

__attribute__((weak))
Current_t MotorThermalModel_Read_MotorCurrent(uint32_t index)
{
    ASSERT(index < 6);
    /* Begin User Code Section: MotorCurrent:read Start */

    /* End User Code Section: MotorCurrent:read Start */
    /* Begin User Code Section: MotorCurrent:read End */

    /* End User Code Section: MotorCurrent:read End */
    return 0.0f;
}

__attribute__((weak))
void MotorThermalModel_Read_ThermalParameters(MotorThermalParameters_t* value)
{
    ASSERT(value != NULL);
    /* Begin User Code Section: ThermalParameters:read Start */

    /* End User Code Section: ThermalParameters:read Start */
    *value = (MotorThermalParameters_t) {
        .resistance    = 0.0f,
        .coeff_cooling = 0.0f,
        .coeff_heating = 0.0f
    };
    /* Begin User Code Section: ThermalParameters:read End */

    /* End User Code Section: ThermalParameters:read End */
}
